"""Simple in-memory registry mapping events to listener implementations."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from .listener import ListenerContract

EventType = str
ListenerName = str


@dataclass
class Registry:
    """Holds mapping from event type to listener names and their implementations."""

    event_to_listeners: Dict[EventType, List[ListenerName]]
    listener_impls: Dict[ListenerName, ListenerContract]

    @classmethod
    def new(cls, event_to_listeners: Dict[EventType, List[ListenerName]], instances: list[ListenerContract]) -> "Registry":
        """Build a Registry from a mapping and a list of listener instances."""
        impls = {inst.name: inst for inst in instances}
        return cls(event_to_listeners=event_to_listeners, listener_impls=impls)

    def listeners_for_event(self, event: EventType) -> list[ListenerName]:
        """Return listener names registered for the given event type."""
        return self.event_to_listeners.get(event, [])

    def impl_for(self, name: ListenerName) -> Optional[ListenerContract]:
        """Return the listener implementation by name if present."""
        return self.listener_impls.get(name)
