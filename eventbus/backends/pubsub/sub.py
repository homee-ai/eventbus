from google.cloud import pubsub_v1
from ...interfaces.base import Subscriber, MessageHandler


class PubSubSubscriber(Subscriber):
    def __init__(self, project_id: str, subscription_id: str, flow_max_messages: int = 100):
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(project_id, subscription_id)
        self._flow = pubsub_v1.types.FlowControl(max_messages=flow_max_messages)
        self._future = None

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        def _cb(message: pubsub_v1.subscriber.message.Message):
            try:
                handler(message.data, dict(message.attributes))
                message.ack()
            except Exception:
                message.nack()

        self._future = self._subscriber.subscribe(self._subscription_path, callback=_cb, flow_control=self._flow)

    def run(self) -> None:
        if self._future:
            self._future.result()

    def stop(self) -> None:
        if self._future:
            self._future.cancel()
        self._subscriber.close()
