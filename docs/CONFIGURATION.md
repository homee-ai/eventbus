# Configuration

This project reads most runtime settings from environment variables. A .env file is supported (loaded via python-dotenv) by the CLI and helper utilities.

## How configuration is loaded
- CLI: eventbus-cli loads .env via eventbus.cli.logging and eventbus.cli.setting
- Python API: Load your own .env before constructing components, or pass values programmatically

## Environment variables
- ENVIRONMENT: Runtime environment name. Affects logging formatter. Default: local
- LOG_LEVEL: Root logger level. Default: INFO

### Google Cloud Pub/Sub
- GCP_PROJECT_ID: Google Cloud project ID
- PUBSUB_TOPIC_NAME: Topic name for primary bus
- PUBSUB_SUBSCRIPTION_NAME: Subscription name for primary bus
- PUBSUB_DLQ_TOPIC_NAME: Topic name for DLQ (dead-letter queue) bus
- PUBSUB_DLQ_SUBSCRIPTION_NAME: Subscription name for DLQ bus

### OpenTelemetry (optional)
- OTLP_ENDPOINT: OTLP HTTP endpoint for traces, e.g. http://localhost:4318/v1/traces
- OTLP_SERVICE_NAME: Logical service name reported to the collector

### Task discovery
- EVENTBUS_TASKS_PACKAGES: Comma-separated list of Python package names to scan for registered task handlers. Default: tasks

## Logging behavior
- In local ENVIRONMENT, logs are formatted in plain text
- In non-local environments, logs are JSON with nested fields and include trace_id and span_id (if tracing is active)

## Credentials for Google Cloud
- Use Application Default Credentials (ADC) or set GOOGLE_APPLICATION_CREDENTIALS to the path of a service account JSON file
- Ensure the service account has Pub/Sub permissions to create/read/write the configured topic/subscription when auto_create=True

## Sample .env
```dotenv
ENVIRONMENT=local
LOG_LEVEL=DEBUG
GCP_PROJECT_ID=your-gcp-project
PUBSUB_TOPIC_NAME=events
PUBSUB_SUBSCRIPTION_NAME=events-sub
PUBSUB_DLQ_TOPIC_NAME=events-dlq
PUBSUB_DLQ_SUBSCRIPTION_NAME=events-dlq-sub
OTLP_ENDPOINT=http://localhost:4318/v1/traces
OTLP_SERVICE_NAME=eventbus-demo
EVENTBUS_TASKS_PACKAGES=tasks
```
