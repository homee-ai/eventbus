# eventbus

A lightweight event bus with pluggable backends (in-memory and Google Cloud Pub/Sub).

## Requirements
- Python 3.12.x (this project is locked to 3.12)
- pip 23+ and virtualenv (recommended)

## Quick start

### 1) Create and activate a virtual environment (recommended)
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip wheel
```

### 2) Install the package (from this repository)
- Regular install:
```bash
pip install .
```
- Editable (development) install:
```bash
pip install -e .
```

This will install the `eventbus` package and its dependencies:
- python-dotenv
- pydantic
- google-cloud-pubsub

### 3) Verify the installation
```bash
python -c "import eventbus; print(eventbus.__name__, 'installed')"
```

## Running the examples
- In-memory backend:
```bash
python examples/example_inmemory.py
```
- Google Cloud Pub/Sub backend:
  - Ensure you have a GCP project and credentials. Set the environment variable to your service account JSON key file:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    ```
  - Configure your Pub/Sub topic/subscription as needed, then run:
    ```bash
    python examples/example_pubsub.py
    ```

## Installing from a Git repository
If you host this repository remotely, you can install directly via pip:
```bash
pip install git+https://github.com/<your-org>/<your-repo>.git#subdirectory=eventbus
```
Replace `<your-org>/<your-repo>` and adjust `subdirectory` if the project lives in a monorepo layout.

## Uninstall
```bash
pip uninstall eventbus
```

## Troubleshooting
- Python version error: Ensure you are using Python 3.12.x. The package declares `requires-python = ">=3.12,<3.13"`.
- Credentials issues with Pub/Sub: Make sure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account JSON with Pub/Sub permissions, and your GCP project/topics exist.
- Dependency installation problems: Upgrade pip and wheel (`python -m pip install -U pip wheel`) and retry.

## Notes on events and examples
- Event types are plain strings (event_type), e.g. "user.registered". The examples use strings throughout.
- Metadata keys published with each message include at minimum: event_type, listener, and priority.
- The EventBus.subscribe() method no longer requires dummy arguments; you can simply call bus.subscribe(). The examples reflect this.

## Development
- Linting/formatting/testing setup is not enforced here; feel free to use your preferred tools.
- Submit PRs/issues with reproduction steps if you run into problems.
