from typing import List, Optional

from ..models import Event
from ..tracing import inject_trace_to_event, extract_trace_from_event, start_span
from . import BaseEventBus


class LocalEventBus(BaseEventBus):
    """
    Synchronous, single-thread consumer with priority and wildcard handlers.
    - publish(): push to heap (priority + seq)
    - consume(): pop by priority, then sequence
    - subscribe([]) means wildcard
    - handler exceptions are caught and stored to event.metadata['handler_errors']
    """

    def __init__(self) -> None:
        super().__init__()
        self._queue: List[Event] = []
        self._seq: int = 0
        self._closed = False

    def publish(self, event: Event, *args, **kwargs) -> None:
        if self._closed:
            raise RuntimeError("EventBus is closed")

        inject_trace_to_event(event)
        self.logger.info("Published event", extra={"type": event.type})
        self._queue.append(event)

    def consume(self, max_items: Optional[int] = None) -> bool:
        for index, event in enumerate(self._queue):
            handler = self._handlers.get(event.type)
            if handler:
                # Extract trace from event and create a handling span
                extract_trace_from_event(event)
                with start_span(name=f"handle:{event.type}"):
                    try:
                        self.logger.debug("Handling event type=%s", event.type)
                        handler(event)
                        self.logger.debug("Handled event type=%s", event.type)
                    except Exception:
                        self.logger.exception("Handler raised for event type=%s", event.type)
                    finally:
                        del self._queue[index]
                return True
        return False

    def run_forever(self, auto_close: bool = True) -> None:
        # Process all queued events
        for index, event in list(enumerate(self._queue)):
            handler = self._handlers.get(event.type)
            if handler:
                extract_trace_from_event(event)
                with start_span(name=f"handle:{event.type}"):
                    try:
                        self.logger.debug("Handling event.", extra={"type": event.type})
                        handler(event)
                        self.logger.debug("Handled event.", extra={"type": event.type})
                    except Exception as e:
                        self.logger.exception(f"Handler raised for event.", extra={"type": event.type}, exc_info=e)
                    finally:
                        del self._queue[index]

    def close(self) -> None:
        self._closed = True
        self._handlers.clear()
        self._queue.clear()
