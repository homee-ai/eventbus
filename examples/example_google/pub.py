import logging
from eventbus.bus.google import PubSubEventBus
from eventbus import Event, EventPriority
from eventbus.tracing import setup_tracing


logging.getLogger('PubSubEventBus').setLevel(logging.DEBUG)
setup_tracing(
    otlp_endpoint="https://otel-collector.dev.housingagent.homee.ai/v1/traces",
    service_name="ben-local-test-event-bus",
)

bus = PubSubEventBus(
    project_id="housing-agent-463406",
    topic_name="ben-local-test",
    auto_create=False,
    nack_on_exception=False
)

logger = logging.getLogger('Runtime')

for i in range(3):
    event = Event(
        type="example_a",
        priority=EventPriority.HIGH,
        detail={"job_id": i + 1, "action": "train-ai"},
    )
    bus.publish(event)
    logger.info(f"[publisher] Published event", extra=event.model_dump())


bus.close()