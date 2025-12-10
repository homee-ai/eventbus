from __future__ import annotations

import json
from typing import Optional, Self

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture

from ..models import Event, EventPriority
from ..tracing import inject_trace_to_event, extract_trace_from_event, start_span
from . import BaseEventBus


def detail_attrs(event: Event) -> dict[str, str]:
    detail = {
        f"event.detail.{k}": str(v)
        for k, v in event.detail.items()
        if v is not None
    }

    return {
        "event.type": event.type,
        "event.priority": event.priority.value,
        **detail,
    }

class PubSubEventBus(BaseEventBus):
    """
    Google Cloud Pub/Sub implementation of the EventBus.

    Supports publishing events to a topic and consuming them via subscription with automatic acknowledgment handling.
    Messages are pulled one at a time with configurable timeout.

    Features:
    - Context Manager interface
    - Auto-creation of topics and subscriptions
    - Configurable message acknowledgment on success/failure 
    - Priority and type-based message routing
    - Wildcard event type subscriptions
    - Resource cleanup on close

    Attributes:
        _BATCH_SIZE (int): Hard limit to always pull exactly 1 message
        _PULL_TIMEOUT (int): Timeout in seconds for pulling messages
    """

    _BATCH_SIZE: int = 1  # hard limit: ALWAYS pull exactly 1
    _PULL_TIMEOUT: Optional[int] = None

    def __init__(
            self,
            project_id: str,
            topic_name: str,
            auto_create: bool = False,
            ack_on_success: bool = True,
            nack_on_exception: bool = True,
            subscription_name: Optional[str] = None,
            filter_types: Optional[list[str]] = None,
    ) -> None:
        """
        :param project_id: GCP Project ID (falls back to env GCP_PROJECT_ID)
        :param topic_name: Pub/Sub topic name
        :param auto_create: Create topic and subscription if absent
        :param ack_on_success: Ack after all handlers succeed
        :param nack_on_exception: Nack immediately when handler raises (else allow redelivery on ack-deadline)
        :param subscription_name: Optional explicit subscription name
        :param filter_types: Optional list of event types to filter this subscription by (Pub/Sub server-side filtering)
        """
        super().__init__()
        self.project_id = project_id
        self.topic_name = topic_name
        # allow overriding subscription name so multiple filtered subscriptions can share the same topic
        self.subscription_name = subscription_name

        self.auto_create = auto_create

        self.ack_on_success = ack_on_success
        self.nack_on_exception = nack_on_exception
        self.filter_types = filter_types

        # Build Pub/Sub filter string if filter_types provided
        self._subscription_filter: Optional[str] = None
        if filter_types:
            exprs = [f'attributes.type="{t}"' for t in filter_types]
            self._subscription_filter = " OR ".join(exprs)

        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(self.project_id, self.topic_name)
        self._ensure_pub_resources()
        self._closed = False

        if self._subscription_filter:
            self.logger.info(f"Pub/Sub subscription filter: {self._subscription_filter}")

        if self.subscription_name:
            self._streaming_pull_future: Optional[StreamingPullFuture] = None
            self._subscriber = pubsub_v1.SubscriberClient()
            self._subscription_path = self._subscriber.subscription_path(self.project_id, self.subscription_name)
            self._ensure_sub_resources()
            self.logger.debug(f"PubSubEventBus initialized: {self._topic_path} / {self._subscription_path}")

    def __enter__(self) -> Self:
        """Allow usage with 'with PubSubEventBus(...) as bus':"""
        self.auto_close = True
        return self

    # -------- EventBus interface --------

    def publish(self, event: Event) -> None:
        if self._closed:
            raise RuntimeError("EventBus is closed")

        # Ensure trace is present in event and log publishing; new trace per publication
        event: Event = inject_trace_to_event(event, new_trace=False)
        event_trace = event.metadata.get("trace", {})
        self.logger.debug(f"Publishing event", extra={"type": event.type})

        data = json.dumps(event.model_dump()).encode("utf-8")
        with start_span(
                name=f"publish:{event.type}",
                trace_id=event_trace.get("trace_id"),
                parent_span_id=event_trace.get("span_id"),
                attributes={
                    "pubsub.topic": self._topic_path,
                    **detail_attrs(event),
                }
        ):
            future = self._publisher.publish(
                self._topic_path,
                data=data,
                type=event.type,
                priority=str(event.priority.value) if hasattr(event, "priority") else EventPriority.NORMAL.value,
            )
            try:
                self.logger.debug(f"Pub/Sub message id: {future.result()}")
                future.result()
            except Exception as e:
                self.logger.error("Failed to publish event", extra={"type": event.type}, exc_info=e)
                raise
            self.logger.info(f"Published event", extra={"type": event.type})

    def consume(self, max_items: Optional[int] = None) -> bool:
        """
        Pull and process EXACTLY 1 message if available.
        - 'max_items' is intentionally ignored (enforced single-message).
        - Returns 1 if a message was processed; otherwise 0.
        """
        if self._closed:
            return False

        response = self._subscriber.pull(
            request={
                "subscription": self._subscription_path,
                "max_messages": self._BATCH_SIZE
            },
            timeout=self._PULL_TIMEOUT,
        )

        if not response.received_messages:
            return False

        rm = response.received_messages[0]
        self._on_message(rm)
        return True

    def run_forever(self, auto_close: bool = False) -> None:
        """ Use streaming pull + auto-extend lease. """
        if self._closed:
            raise RuntimeError("EventBus is closed")

        self.logger.info("Starting PubSubEventBus streaming worker...")

        flow_control = pubsub_v1.types.FlowControl(
            max_messages=self._BATCH_SIZE,
        )

        with self._subscriber:
            self._streaming_pull_future = self._subscriber.subscribe(
                self._subscription_path,
                callback=self._on_message,
                flow_control=flow_control,
            )
            self.logger.debug(f"Listening for messages on {self._subscription_path}")

            try:
                self._streaming_pull_future.result()
            except KeyboardInterrupt:
                self.logger.info("Stopping worker (KeyboardInterrupt)")
            except Exception as e:
                self.logger.exception("Streaming pull terminated with error", exc_info=e)
            finally:
                if self._streaming_pull_future:
                    self._streaming_pull_future.cancel()
                    try:
                        self._streaming_pull_future.result(timeout=5)
                    except Exception:
                        pass
                if auto_close or getattr(self, "auto_close", False):
                    try:
                        self.close()
                    except Exception:
                        self.logger.exception("Error during close() in run_forever()")

    def close(self) -> None:
        self._closed = True
        self._subscriber.close()
        self._handlers.clear()

    # -------- internals --------

    def _on_message(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """
        when callback is called, a message will automatically be suspended for lease extension.
        """
        try:
            event: Event = self._decode_message(message.data)
            handler = self.get_with_wildcard(self._handlers, event.type)
            # Extract trace and create a handling span
            trace_id, span_id=extract_trace_from_event(event)
            if not handler and self.filter_types:
                self.logger.warning("No handler for event", extra={"type": event.type})
                message.ack()
                return
            with start_span(
                    name=f"handle:{event.type}",
                    trace_id=trace_id,
                    parent_span_id=span_id,
                    attributes={
                        "pubsub.subscription": self._subscription_path,
                        **detail_attrs(event),
                    }
            ):
                self.logger.debug(f"Handling event", extra={"type": event.type})
                self._invoke_handler(handler, event)
                self.logger.debug("Handled event", extra={"type": event.type})

            if self.ack_on_success:
                message.ack()
            else:
                self.logger.debug("Processed message, but ack_on_success=False. Skip ack.")
        except ValueError:
            event = self._decode_message(message.data)
            self.logger.warning(f"Invalid message format, skipping. {event.type}")
        except Exception:
            self.logger.exception("Exception during streaming message handling")
            if self.nack_on_exception:
                message.nack()
            else:
                self.logger.warning(
                    "Handler failed, nack_on_exception=False; leaving message un-acked."
                )

    def _ensure_pub_resources(self) -> None:
        # Topic
        try:
            self._publisher.get_topic(request={"topic": self._topic_path})
        except Exception:
            if not self.auto_create:
                raise
            try:
                self._publisher.create_topic(request={"name": self._topic_path})
            except AlreadyExists:
                pass
    def _ensure_sub_resources(self) -> None:
        # Subscription
        try:
            sub = self._subscriber.get_subscription(request={"subscription": self._subscription_path})
            # If subscription exists but filter desired and differs, update it
            if self._subscription_filter is not None and getattr(sub, "filter", None) != self._subscription_filter:
                try:
                    self._subscriber.update_subscription(request={
                        "subscription": {"name": self._subscription_path, "filter": self._subscription_filter},
                        "update_mask": {"paths": ["filter"]},
                    })
                    self.logger.info("Updated existed subscription filter", extra={"subscription": self._subscription_path})
                except Exception:
                    self.logger.exception("Failed to update subscription filter")
        except Exception:
            if not self.auto_create:
                self.logger.exception("Failed to get subscription, and auto_create=False", exc_info=True, extra={"subscription": self._subscription_path})

            req = {"name": self._subscription_path, "topic": self._topic_path}
            if self._subscription_filter:
                req["filter"] = self._subscription_filter
            try:
                self._subscriber.create_subscription(request=req)
            except AlreadyExists:
                pass

    @staticmethod
    def _decode_message(data: bytes) -> Event:
        payload = json.loads(data.decode("utf-8"))
        return Event.model_validate(payload)
