"""Dispatcher responsible for routing payloads to listener-specific messages.

It uses Registry to find which listener(s) are interested in the event_type and
publishes one message per listener with appropriate metadata so the Processor
can invoke the correct listener implementation.
"""
import json
from typing import Optional, Dict
from .registry import Registry
from .base import Publisher


class DispatchConfig:
    """Configuration for Dispatcher.

    - topic: destination topic or channel
    - base_attributes: attributes included with every published message
    """

    def __init__(self, topic: str = "events", base_attributes: Optional[Dict[str, str]] = None):
        self.topic = topic
        self.base_attributes = base_attributes or {}


class Dispatcher:
    """High-level publisher that fans out a single event to multiple listeners."""

    def __init__(self, publisher: Publisher, registry: Registry, cfg: Optional[DispatchConfig] = None):
        self.publisher = publisher
        self.registry = registry
        self.cfg = cfg or DispatchConfig()

    def dispatch(self, event_type: str, payload: dict, attributes: Optional[Dict[str, str]] = None) -> None:
        """Publish the payload for each listener registered to the event_type.

        Metadata will always include:
        - event_type: the provided event type
        - listener: the specific listener name (set per message)
        """
        listeners = self.registry.listeners_for_event(event_type)
        if not listeners:
            raise ValueError(f"No listeners for event_type={event_type}")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        base = dict(self.cfg.base_attributes)
        if attributes:
            base.update(attributes)
        base.setdefault("event_type", event_type)

        for ln in listeners:
            meta = dict(base)
            meta["listener"] = ln
            self.publisher.publish(self.cfg.topic, body, metadata=meta)
