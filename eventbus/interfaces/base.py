"""Core interfaces for the event bus.

Defines lightweight protocols for Publisher/Subscriber and an abstract EventBus
contract, used by different backends. This file intentionally avoids any
backend-specific imports to keep dependencies minimal.
"""
from abc import ABC, abstractmethod
from typing import Protocol, Callable, Iterable, Optional, Dict
from ..models import Event


class MessageHandler(ABC):
    @abstractmethod
    def __call__(self, message: bytes, metadata: Dict[str, str]) -> None: ...


class Publisher(Protocol):
    """Minimal publishing protocol.

    Implementations should deliver the message and attach provided metadata
    (attributes) to the message if the backend supports it.
    """

    def publish(self, topic: str, message: bytes, metadata: Optional[Dict[str, str]] = None) -> None: ...


class Subscriber(Protocol):
    """Minimal subscribing protocol.

    Implementations should call the provided handler for each incoming message.
    `run()` may block the current thread, and `stop()` should cancel it.
    """

    def subscribe(self, topic: str, handler: MessageHandler) -> None: ...
    def run(self) -> None: ...
    def stop(self) -> None: ...


class EventBus(ABC):
    """High-level bus that works with domain Events."""

    @abstractmethod
    def publish(self, event: Event, attributes: Optional[Dict[str, str]] = None) -> None: ...

    @abstractmethod
    def subscribe(self, event_types: Optional[Iterable[str]] = None, handler: Optional[Callable[[Event], None]] = None) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
