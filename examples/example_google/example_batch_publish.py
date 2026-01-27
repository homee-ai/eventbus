import logging
from eventbus.bus.google import PubSubEventBus
from eventbus import Event, EventPriority
import time

logging.getLogger("batch_example").setLevel(logging.DEBUG)

start = time.time()
bus = PubSubEventBus(
    project_id="housing-agent-463406",
    topic_name="ben-local-test",
    auto_create=True,
    nack_on_exception=False,
)

logger = logging.getLogger("Runtime")

for i in range(2000):
    event = Event(
        type="example_a",
        priority=EventPriority.HIGH,
        detail={"job_id": i + 1, "action": "train-ai"},
    )
    bus.publish(event)
    logger.info("[publisher] Published event", extra=event.model_dump())

bus.close()
end = time.time()
print(f"Time taken with one by one: {end - start}")

start = time.time()
bus = PubSubEventBus(
    project_id="housing-agent-463406",
    topic_name="ben-local-test",
    auto_create=True,
    nack_on_exception=False,
)

events = [ Event(
        type="example_a",
        priority=EventPriority.HIGH,
        detail={"job_id": i + 1, "action": "train-ai"},
    ) for i in range(2000)]

bus.publish(events)

bus.close()
end = time.time()
print(f"Time taken with batch: {end - start}")