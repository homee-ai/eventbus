# Command Line Interface (CLI)

The eventbus-cli provides utilities to publish events and run workers based on registered task handlers.

## Installation
- Installed automatically with this package (see entry point in pyproject.toml)

## Commands

### show-config
Show current configuration and discovered task handlers.

```bash
eventbus-cli show-config
```

- Loads environment from .env
- Prints settings and registry contents (task name -> file and function info)

### publish
Publish a single event to the primary topic.

```bash
eventbus-cli publish --type <EVENT_TYPE> [--payload '{"k": "v"}']
```

Arguments
- --type: Required event type string
- --payload: Optional JSON object string; must be a valid JSON object (e.g. '{"x": 1}')

Environment required
- GCP_PROJECT_ID
- PUBSUB_TOPIC_NAME
- PUBSUB_SUBSCRIPTION_NAME (used as default subscription name when constructing the bus)

Optional
- OTLP_ENDPOINT, OTLP_SERVICE_NAME for tracing

### worker
Start a long-running worker that consumes events and dispatches them to selected tasks.

```bash
eventbus-cli worker --registry-job-name <TASK_NAME> [--registry-job-name <TASK_NAME> ...]
```

- Resolves functions registered via @register("TASK_NAME")
- Subscribes the PubSubEventBus to those event types
- Runs streaming pull until interrupted

### dlq-worker
Start a long-running DLQ worker for the DLQ topic + subscription.

```bash
eventbus-cli dlq-worker --registry-job-name <TASK_NAME> [--registry-job-name <TASK_NAME> ...]
```

- Resolves functions registered via @dlq_register("TASK_NAME")
- Uses PUBSUB_DLQ_TOPIC_NAME and PUBSUB_DLQ_SUBSCRIPTION_NAME

## Task registration & discovery
Decorate handlers in your application code:

```python
from eventbus.cli.registry import register, dlq_register
from eventbus.models import Event

@register("user_registered")
def on_user_registered(event: Event):
    ...

@dlq_register("user_registered")
def on_user_registered_dlq(event: Event):
    ...
```

- The CLI auto-discovers modules from packages listed in EVENTBUS_TASKS_PACKAGES (comma-separated). Default: tasks
- Ensure the packages are importable (PYTHONPATH includes project root)

## Logging and tracing
- CLI configures logging based on ENVIRONMENT and LOG_LEVEL
- If OTLP_ENDPOINT is set, OpenTelemetry tracing is enabled and trace/span IDs are injected into logs

## Troubleshooting
- Invalid JSON payload: Ensure --payload is a valid JSON object string
- Task not found: Use eventbus-cli show-config to list discovered tasks
- Pub/Sub permission issues: Ensure ADC or GOOGLE_APPLICATION_CREDENTIALS is set and has necessary Pub/Sub roles
