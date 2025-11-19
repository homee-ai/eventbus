# EventBus Demo (Google Pub/Sub)

A small, runnable demo that shows how to:
- Publish events to Google Cloud Pub/Sub using the eventbus library
- Run a worker that consumes events and dispatches them to registered jobs
- Chain jobs by publishing new events from a handler

The demo includes two example jobs:
- `amazing_ai.crawler`: fetches a URL and publishes its result as another event
- `amazing_ai.result`: logs the origin URL and the output length from the crawler


## Prerequisites
- Python 3.12
- A Google Cloud project with Pub/Sub enabled
- Credentials for Google Cloud
```bash
gcloud auth application-default login
```
- (Optional) An OTLP-compatible collector endpoint if you want to send tracing spans


## Project layout
- demo/cli.py: Command-line entry that exposes publish, worker, and show-config commands
- demo/handler.py: Implements the logic for those CLI commands and wiring to the bus
- demo/setting.py: Loads environment variables (.env supported)
- demo/tasks/: Two example job handlers and a job registry
- Dockerfile: Convenience container for running the demo without installing locally


## Install and run locally

1) Change into the demo directory
    ```bash
   cd examples/demo
    ```
2) Install dependencies
    ```bash
     brew install poetry
     poetry install
    ```

   3) Configure environment
      Copy the provided .env template (already present) and update it with your values:
       ``` .dotenv
      GCP_PROJECT_ID="your-gcp-project"
      PUBSUB_TOPIC_NAME="your-topic"
      PUBSUB_SUBSCRIPTION_NAME="your-sub"
      OTLP_ENDPOINT="https://your-otel-collector/v1/traces"  # optional
      OTLP_SERVICE_NAME="demo"                               # optional
       ```
      Authentication options:
      - If you already have Application Default Credentials (adc):
        ```bash
        gcloud auth application-default login
        # No extra env is needed if running locally with ADC
        ```
      - (NOT RECOMMENDED) Or use a service account key JSON:
        ```
        export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
        ```
4) Show config (sanity check)
    ```
   poetry run eventbus-cli show-config
   # or, if using pip/venv:
   eventbus-cli show-config
   ```
   example output
    ```dotenv
                                          Config                                      
    ┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Key               ┃ Value                                                      ┃
    ┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ project_id        │ housing-agent-463406                                       │
    │ topic_id          │ ben-local-test                                             │
    │ subscription_id   │ ben-local-test-sub                                         │
    │ otlp_endpoint     │ https://otel-collector.dev.housingagent.homee.ai/v1/traces │
    │ otlp_service_name │ demo                                                       │
    └───────────────────┴────────────────────────────────────────────────────────────┘
    ```

5) Start a worker
   You must declare which jobs from demo.tasks.job_registry you want to run. For the example chain (crawler -> result), run:
    ```bash
   poetry run eventbus-cli worker \
     --registry-job-name amazing_ai.crawler \
     --registry-job-name amazing_ai.result
    ```
   The worker will connect to the configured Pub/Sub subscription and wait for events. Keep this terminal open.

6) Publish an event
   In another terminal window:
    ```bash
   poetry run eventbus-cli publish \
     --type amazing_ai.crawler \
     --payload '{"url":"https://example.com"}'
    ```
   The crawler job will fetch the URL, then publish amazing_ai.result. The result job will log the origin URL and the output length.


## Docker usage

Build the demo image from the demo directory:
  ```
  cd examples/demo
  ssh-add ~/.ssh/id_ed25519 # ur github private key
  ssh-add -l # check that it's added
  ```
  example output:
  ```
  256 SHA256:xxxxxxxxxxx/yyyyyyyyyyy benliu@Mac.localdomain (ED25519)
  ```
  build the image:
  ```
  docker build --ssh default -t eventbus-demo . --platform linux/amd64
  ```

## Notes on Pub/Sub resources
- The demo bus uses auto_create=True, so it will try to create the topic and subscription if missing.
- Ensure your credentials have `pubsub.editor` (or sufficient) permissions for the project.


## Troubleshooting
- Job 'xyz' not found in registry: The worker only accepts names defined in `demo/tasks/__init__.py` under `job_registry`. Use `amazing_ai.crawler` and/or `amazing_ai.result`, or add your own.
- Invalid JSON payload: The publish command expects a JSON object string (e.g., '{"x":1}').
- PermissionDenied / NotFound (Pub/Sub): Check GCP project ID, topic/subscription names, and credentials.
- No logs from result: Make sure you started the worker with both crawler and result jobs; the crawler publishes amazing_ai.result which the result job consumes.
- Tracing: If OTLP_ENDPOINT is set, spans will be exported. If not, tracing is simply disabled.


## Extending the demo
- Add new tasks in demo/tasks and register them in `demo/tasks/__init__.py`
- Publish new event types with `eventbus-cli publish --type your.type --payload '{...}'`
