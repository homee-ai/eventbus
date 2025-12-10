# EventBus for Python — Local and Google Cloud Pub/Sub

A lightweight event bus abstraction with:
- Unified Event model with priority and metadata
- Two implementations: in‑process LocalEventBus and Google Cloud Pub/Sub (PubSubEventBus)
- Optional OpenTelemetry tracing (OTLP) with trace/span IDs injected into logs
- JSON logs in non‑local environments, human‑friendly text logs in local
- Simple CLI to publish events and run workers

Requirements
- Python 3.12 (>=3.12,<3.13)
- For Pub/Sub: Google Application Default Credentials (ADC) or a service account JSON key available to the process

Installation
- Using pip from source: pip install -e .
- Or with Poetry: poetry install

Quickstart
1) Local (in‑process) bus

    from eventbus import Event, EventPriority
    from eventbus.bus.local import LocalEventBus
    import logging

    logging.getLogger("LocalEventBus").setLevel(logging.DEBUG)

    def handle_test(event: Event):
        logging.getLogger("handler").info("Handled", extra=event.model_dump())

    bus = LocalEventBus()
    bus.subscribe({"test": handle_test})
    bus.publish(Event(type="test", priority=EventPriority.HIGH, detail={"x": 1}))
    bus.consume()  # processes queued events once
    bus.close()

2) Google Cloud Pub/Sub

    from eventbus.bus.google import PubSubEventBus
    from eventbus import Event, EventPriority
    from eventbus.tracing import setup_tracing

    setup_tracing(
        otlp_endpoint="http://localhost:4318/v1/traces",  # optional
        service_name="eventbus-demo",
    )

    with PubSubEventBus(
        project_id="your-gcp-project",
        topic_name="events",
        subscription_name="events-sub",
        auto_create=True,  # creates topic/sub if missing
    ) as bus:
        bus.publish(Event(type="user.registered", priority=EventPriority.NORMAL, detail={"user_id": 42}))

CLI
The package ships a small CLI to publish events and run workers.

- Publish one event:
  eventbus-cli publish --type user.registered --payload '{"user_id": 42}'

- Start a worker for selected task names:
  eventbus-cli worker --registry-job-name user_registered_handler

- Start a DLQ worker:
  eventbus-cli dlq-worker --registry-job-name user_registered_handler

- Show effective configuration and discovered tasks:
  eventbus-cli show-config

Handlers registry and auto‑discovery
- Register handlers using decorators provided by eventbus.cli.registry:

    from eventbus.cli.registry import register, dlq_register
    from eventbus.models import Event

    @register("user_registered_handler")
    def handle_user_registered(event: Event):
        ...

- The CLI discovers tasks by importing modules from packages listed in EVENTBUS_TASKS_PACKAGES (comma‑separated). Defaults to tasks.
- Valid handler signatures:
  - (event: Event)
  - (bus: BaseEventBus | Subclass | Optional[…], event: Event)
  - (event: Event, bus: BaseEventBus | Subclass | Optional[…])

Configuration
- Most settings are read from environment variables (with .env support). See CONFIGURATION.md for the full list and defaults.

Tracing and logging
- setup_tracing enables OTLP export and injects real trace/span IDs into logs.
- Without OTLP, synthetic IDs are still carried in Event.metadata for correlation.
- Logs are JSON in non‑local environments and plain text in local.

Documentation
- USAGE.md — Python API examples and patterns
- CLI.md — All CLI commands and examples
- CONFIGURATION.md — Environment variables (.env)
- ARCHITECTURE.md — Components and data flow
- CONTRIBUTING.md — How to work on this repo

Examples
- See the examples/ directory:
  - examples/example_local.py
  - examples/example_google/pub.py

License
- This repository currently does not include a license file. Add one if you plan to distribute the package.
