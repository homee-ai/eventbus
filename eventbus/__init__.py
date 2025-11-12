"""EventBus package public API.

This module re-exports the most commonly used types so users can import
from `eventbus` directly if desired.
"""

from .models import Event, Priority
from .interfaces.base import EventBus, Publisher, Subscriber
from .interfaces.dispatcher import Dispatcher, DispatchConfig
from .interfaces.registry import Registry
from .interfaces.processor import Processor
from .config import build_eventbus

__all__ = [
    # Models
    "Event",
    "Priority",
    # Core interfaces
    "EventBus",
    "Publisher",
    "Subscriber",
    # Orchestration
    "Dispatcher",
    "DispatchConfig",
    "Registry",
    "Processor",
    # Builders
    "build_eventbus",
]
