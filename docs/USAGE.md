# Usage (Python API)

This guide shows how to use the Python API provided by this package. For the command-line interface, see docs/CLI.md.

## Core concepts
- Event: Pydantic model with fields type, priority, detail, and metadata
- EventBus: Interface with publish, subscribe, consume, unsubscribe, and close
- Implementations: LocalEventBus (in-process) and PubSubEventBus (Google Cloud Pub/Sub)
- Handlers: Functions that process events; they can optionally receive the bus as an argument

## Event model
```python
from eventbus.models import Event, EventPriority

event = Event(
    type="user.registered",
    priority=EventPriority.NORMAL,
    detail={"user_id": 42},
)
```

## Handler signatures
Valid handler signatures (type hints are validated by the CLI registry helpers and used by BaseEventBus):
- def h(event: Event) -> None
- def h(bus: BaseEventBus, event: Event) -> None
- def h(event: Event, bus: BaseEventBus) -> None

## LocalEventBus (in-process)
```python
from eventbus.bus.local import LocalEventBus
from eventbus.models import Event, EventPriority

bus = LocalEventBus()

def handle_user_registered(event: Event):
    print("user registered:", event.detail)

bus.subscribe({"user.registered": handle_user_registered})

bus.publish(Event(type="user.registered", detail={"user_id": 42}))
bus.consume()  # process queued events
bus.close()
```

### Wildcard subscriptions
BaseEventBus provides get_with_wildcard used internally by LocalEventBus and PubSubEventBus. You can subscribe using explicit types; wildcard matching is used during handler lookup, so a handler registered under patterns like "user.*" will be matched when dispatching (already done in PubSubEventBus and run_forever()).

## Google Cloud Pub/Sub
```python
from eventbus.bus.google import PubSubEventBus
from eventbus.models import Event

with PubSubEventBus(
    project_id="your-gcp-project",
    topic_name="events",
    subscription_name="events-sub",
    auto_create=True,
) as bus:
    bus.publish(Event(type="user.registered", detail={"user_id": 42}))
```

### Worker mode
```python
from eventbus.bus.google import PubSubEventBus
from eventbus.models import Event

def handle_user_registered(event: Event):
    print("user registered:", event.detail)

with PubSubEventBus(
    project_id="your-gcp-project",
    topic_name="events",
    subscription_name="events-sub",
) as bus:
    bus.subscribe({"user.registered": handle_user_registered})
    bus.run_forever()
```

## Tracing
- Optional OpenTelemetry tracing can be enabled via eventbus.tracing.setup_tracing
- Trace/span IDs are injected into logs and propagated via Event.metadata

```python
from eventbus.tracing import setup_tracing, start_span, shutdown_tracing
from eventbus.bus.local import LocalEventBus
from eventbus.models import Event

setup_tracing(
    otlp_endpoint="http://localhost:4318/v1/traces",
    service_name="eventbus-demo",
)

bus = LocalEventBus()

with start_span("do-work"):
    bus.publish(Event(type="job.started", detail={"id": 1}))

shutdown_tracing()
```

## Logging
- Logging configuration is provided in eventbus.logging.LOGGING_CONFIG
- The CLI sets this up automatically based on ENVIRONMENT and LOG_LEVEL; in library usage, configure Python logging as you prefer and/or reuse LOGGING_CONFIG

## Task registry helpers (for CLI workers)
The CLI uses a registry of handler functions to start workers for selected tasks.

```python
from eventbus.cli.registry import register, dlq_register
from eventbus.models import Event

@register("task_name")
def h(event: Event):
    ...  # handle primary topic events

@dlq_register("task_name")
def h_dlq(event: Event):
    ...  # handle DLQ events
```

## Auto-discovery
- The CLI discovers tasks by importing modules from packages named in EVENTBUS_TASKS_PACKAGES (comma-separated). Default: tasks
- Ensure your package is importable (PYTHONPATH includes its parent), and that importing your modules registers the tasks
