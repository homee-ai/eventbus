"""
Registry module for managing task handler functions.

Handlers can be registered using @register and stored in REGISTRY.

Valid handler signatures:
    (event: Event)
    (bus: BaseEventBus | Subclass | Optional[…], event: Event)
    (event: Event, bus: BaseEventBus | Subclass | Optional[…])
"""

import inspect
import types
from collections import defaultdict
from typing import Dict, get_type_hints, get_origin, get_args, Union

from eventbus.bus import EventName, EventHandlerWithBus, EventHandlerSimple

REGISTRY: Dict[EventName, EventHandlerWithBus | EventHandlerSimple] = defaultdict()
DLQ_REGISTRY: Dict[EventName, EventHandlerWithBus | EventHandlerSimple] = defaultdict()


class RegistryError(Exception): ...


def _is_event_type(t) -> bool:
    from eventbus.models import Event

    return isinstance(t, type) and issubclass(t, Event)


def _is_bus_like_type(t) -> bool:
    """Return True if t is BaseEventBus, its subclass, or an Optional/Union containing it."""
    from eventbus.bus import BaseEventBus

    if t is None:
        return False

    if isinstance(t, type) and issubclass(t, BaseEventBus):
        return True

    origin = get_origin(t)
    if origin in (types.UnionType, Union):
        args = get_args(t)
        if type(None) not in args:
            return False

        non_none = [a for a in args if a is not type(None)]
        if len(non_none) != 1:
            return False

        actual = non_none[0]
        return isinstance(actual, type) and issubclass(actual, BaseEventBus)

    return False


def register(task_name: str):
    """Register a handler function under the specified task name."""

    def decorator(func: EventHandlerWithBus | EventHandlerSimple):
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        hints = get_type_hints(func, globalns=func.__globals__)

        # ---- One-argument handler must be (event: Event) ----
        if len(params) == 1:
            p = params[0]
            if not _is_event_type(hints.get(p.name)):
                raise RegistryError(
                    f"Invalid handler for '{task_name}': single parameter must be Event."
                )

        # ---- Two-argument handler: must contain one Event and one Bus-like ----
        elif len(params) == 2:
            p1, p2 = params
            t1 = hints.get(p1.name)
            t2 = hints.get(p2.name)

            valid = (_is_bus_like_type(t1) and _is_event_type(t2)) or (
                _is_event_type(t1) and _is_bus_like_type(t2)
            )

            if not valid:
                raise RegistryError(
                    f"Invalid handler for '{task_name}': must include one Event and one BaseEventBus."
                )

        # ---- Invalid parameter count ----
        else:
            raise RegistryError(
                f"Invalid handler for '{task_name}': must have 1 or 2 parameters."
            )

        REGISTRY[task_name] = func
        return func

    return decorator

def dlq_register(task_name: str):
    """Register a handler function under the specified task name."""

    def decorator(func: EventHandlerWithBus | EventHandlerSimple):
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        hints = get_type_hints(func, globalns=func.__globals__)

        # ---- One-argument handler must be (event: Event) ----
        if len(params) == 1:
            p = params[0]
            if not _is_event_type(hints.get(p.name)):
                raise RegistryError(
                    f"Invalid handler for '{task_name}': single parameter must be Event."
                )

        # ---- Two-argument handler: must contain one Event and one Bus-like ----
        elif len(params) == 2:
            p1, p2 = params
            t1 = hints.get(p1.name)
            t2 = hints.get(p2.name)

            valid = (_is_bus_like_type(t1) and _is_event_type(t2)) or (
                _is_event_type(t1) and _is_bus_like_type(t2)
            )

            if not valid:
                raise RegistryError(
                    f"Invalid handler for '{task_name}': must include one Event and one BaseEventBus."
                )

        # ---- Invalid parameter count ----
        else:
            raise RegistryError(
                f"Invalid handler for '{task_name}': must have 1 or 2 parameters."
            )

        DLQ_REGISTRY[task_name] = func
        return func

    return decorator
