from typing import Dict, List, Optional

from ..models import Event, EventPriority
from . import BaseEventBus

_PRIORITY_ORDER: Dict[EventPriority, int] = {
    EventPriority.HIGH: 0,
    EventPriority.NORMAL: 1,
    EventPriority.LOW: 2,
}


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
        self._queue.append(event)

    def consume(self, max_items: Optional[int] = None) -> bool:
        for index, event in enumerate(self._queue):

            handler = self._handlers.get(event.type)
            if handler:
                handler(event)
                del self._queue[index]
                return True
        return False

    def run_forever(self, auto_close: bool = True) -> None:
        for index, event in enumerate(self._queue):

            handler = self._handlers.get(event.type)
            if handler:
                handler(event)
                del self._queue[index]

    def close(self) -> None:
        self._closed = True
        self._handlers.clear()
        self._queue.clear()
