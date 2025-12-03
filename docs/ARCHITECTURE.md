# Architecture

This document describes the main components of the EventBus project and how they interact.

## Components
- Models (eventbus/models.py)
  - Event: Pydantic model describing an event (type, priority, detail, metadata)
  - EventPriority: Enum for high/normal/low

- Bus Abstractions (eventbus/bus/__init__.py)
  - EventBus Protocol: publish, subscribe, consume, unsubscribe, close
  - BaseEventBus: common logic for managing handler mapping and with-context support
    - subscribe/unsubscribe: register handlers by event name
    - _invoke_handler: calls handler with correct signature (event or bus,event)
    - get_with_wildcard: simple fnmatch-based wildcard matching for event types

- LocalEventBus (eventbus/bus/local.py)
  - In-memory queue for published events
  - Synchronous processing via consume() and run_forever()
  - Injects/extracts tracing context for every event
  - Logs handler execution and catches exceptions

- PubSubEventBus (eventbus/bus/google.py)
  - Google Cloud Pub/Sub implementation
  - Publishes JSON-encoded Event with attributes (type, priority)
  - Consumes via pull() (single message) or streaming run_forever()
  - Auto-creates topic/subscription when auto_create=True
  - Supports server-side filtering via filter_types (attributes.type="…")
  - Acknowledgment strategy controlled by ack_on_success and nack_on_exception

- Tracing (eventbus/tracing.py)
  - Optional OpenTelemetry integration; falls back to synthetic IDs if unavailable
  - setup_tracing configures OTLP exporter and tracer provider
  - start_span context manager; get_trace_ids reads current span IDs
  - inject_trace_to_event/extract_trace_from_event put/retrieve trace info in Event.metadata

- Logging (eventbus/logging.py)
  - JSON formatter for non-local environments (includes nested fields and trace/span IDs)
  - Plain-text formatter for local
  - OTELTraceFilter injects current trace/span IDs from OTel context into logging records

- CLI (eventbus/cli/*)
  - cli.py: argument parsing and command dispatch
  - handler.py: implementations for show-config, publish, worker, dlq-worker
  - registry.py: decorators @register and @dlq_register for task registration with signature checks
  - discover.py: auto-discovers task modules from packages listed in EVENTBUS_TASKS_PACKAGES
  - logging.py and setting.py: load .env and configure logging dynamically

Data flow examples
1) Publishing (Local)
- User calls LocalEventBus.publish(Event)
- Tracing data is injected into Event.metadata
- Event is queued in memory
- consume() pops and dispatches to a matching handler (exact or wildcard)

2) Publishing (Pub/Sub)
- Event is serialized to JSON and published to topic with attributes
- If setup_tracing was called, a span is created for publish and IDs are logged

3) Consuming (Pub/Sub)
- run_forever() starts streaming pull with a callback
- For each message: decode -> extract trace -> start handling span -> invoke handler
- Ack/nack according to configuration

Error handling
- LocalEventBus catches and logs handler exceptions during consume/run_forever
- PubSubEventBus catches and logs within _on_message; can nack on exception
- Logging captures trace/span IDs for correlation

Extending the system
- Add new bus implementations by subclassing BaseEventBus and implementing publish, consume, and close
- Use get_with_wildcard for flexible handler matching
- Add new CLI commands by updating cli.py and handler implementations

Performance notes
- LocalEventBus is single-threaded and intended for testing or simple pipelines
- PubSubEventBus enforces single message in-flight (max_messages=1) for predictability; adjust in code if you need higher concurrency, considering handler idempotence and acking strategy
