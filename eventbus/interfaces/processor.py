"""Processor resolves a listener from attributes and invokes it.

Backends can delegate message handling to this component so they remain thin.
Expected attributes include a 'listener' key set by Dispatcher.
"""
from typing import Dict
from .registry import Registry


class Processor:
    def __init__(self, registry: Registry):
        self.registry = registry

    def process(self, message: bytes, attributes: Dict[str, str]) -> None:
        listener_name = attributes.get("listener")
        if not listener_name:
            raise ValueError("Missing 'listener' attribute")
        impl = self.registry.impl_for(listener_name)
        if impl is None:
            raise RuntimeError(f"Listener not found: {listener_name}")
        impl.handle(message, context={"attributes": attributes})
