from abc import ABC, abstractmethod
import logging
from types import TracebackType
from typing import Type, Optional
from typing import Protocol, Iterable, Callable, runtime_checkable, Self
from ..models import Event


EventHandlerWithBus = Callable[[Optional["BaseEventBus"], "Event"], None]
EventHandlerSimple = Callable[["Event"], None]

EventName = str

EventMapping = dict[EventName, EventHandlerWithBus | EventHandlerSimple]

@runtime_checkable
class EventBus(Protocol):
    def publish(self, event: Event) -> None: ...

    def subscribe(self, event_mapping: EventMapping) -> None: ...

    def consume(self, max_items: int | None = None) -> bool: ...

    def unsubscribe(self, event_types: Optional[Iterable[str]] = None) -> None: ...

    def close(self) -> None: ...


class BaseEventBus(ABC, EventBus):
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._handlers: EventMapping = {}
        self.auto_close = False

    @abstractmethod
    def publish(self, event: Event) -> None:
        ...

    @abstractmethod
    def consume(self, max_items: int | None = None) -> bool:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def subscribe(self, event_handlers: EventMapping) -> None:
        self._handlers.update(event_handlers)

    def unsubscribe(self, event_types: Iterable[str] = None) -> None:
        for event_type in event_types:
            self._handlers.pop(event_type, None)

    def __enter__(self) -> Self:
        """Allow usage with 'with PubSubEventBus(...) as bus':"""
        return self

    def __exit__(
            self,
            exc_type: Type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> bool:
        """Ensure resources are always released on exit."""
        try:
            self.close()
        except Exception:
            self.logger.exception("Error during close() in __exit__")
        if exc_type:
            self.logger.exception(f"Exited with exception: {exc_type.__name__}: {exc_val}")
        else:
            self.logger.info("EventBus closed cleanly.")
        return False

    def _invoke_handler(self, handler: EventHandlerSimple | EventHandlerWithBus, event: Event) -> None:
        """Internal method to invoke a handler, auto-detecting signature."""
        import inspect
        sig = inspect.signature(handler)

        # Check number of parameters
        if len(sig.parameters) == 1:
            # Simple handler: handler(event)
            handler(event)
        else:
            # Advanced handler: handler(bus, event)
            handler(self, event)