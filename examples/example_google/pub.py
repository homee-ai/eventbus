import logging
from eventbus.bus.google import PubSubEventBus
from eventbus import Event, EventPriority


logging.getLogger("PubSubEventBus").setLevel(logging.DEBUG)

bus = PubSubEventBus(
    project_id="housing-agent-463406",
    topic_name="ben-local-test",
    auto_create=False,
    nack_on_exception=False,
)

logger = logging.getLogger("Runtime")

for i in range(3):
    event = Event(
        type="example_a",
        priority=EventPriority.HIGH,
        detail={"job_id": i + 1, "action": "train-ai"},
    )
    bus.publish(event)
    logger.info("[publisher] Published event", extra=event.model_dump())


bus.close()
