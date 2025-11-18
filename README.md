EventBus minimal tracing and logging

Features:
- Context-based trace_id/span_id injected into logs.
- Optional OpenTelemetry (OTLP) export to a collector.

Usage
-----

Basic logging with trace fields:

    from eventbus.logging import setup_basic_logging
    setup_basic_logging()

OpenTelemetry setup (optional):

    from eventbus.tracing import setup_tracing, start_span

    # Configure OTLP HTTP exporter (4318) to your collector
    setup_tracing(
        otlp_endpoint="http://localhost:4318/v1/traces",
        service_name="eventbus-demo",
    )

    # Create a span – logs inside will show real trace/span ids
    with start_span("demo"):  # spans are exported when OTLP is configured
        ...

Shutting down (flush exporter):

    from eventbus.tracing import shutdown_tracing
    shutdown_tracing()

Notes
-----
- If OpenTelemetry packages are not installed, tracing still works for logs and for propagating trace_id/span_id in Event.metadata, but no spans will be exported.
- To install OpenTelemetry dependencies:

    pip install "opentelemetry-sdk>=1.27" "opentelemetry-exporter-otlp>=1.27"

- The event metadata includes a "trace" dict with trace_id and span_id. Handlers use this to continue traces across publish/consume.
