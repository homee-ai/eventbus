from eventbus.bus.google import PubSubEventBus
from eventbus import Event, EventPriority

bus = PubSubEventBus(
    project_id="housing-agent-463406",
    topic_name="test",
    prefix="ben-local",
    auto_create=False,
    nack_on_exception=False
)



for i in range(3):
    event = Event(
        type="example_a",
        priority=EventPriority.HIGH,
        detail={"job_id": i + 1, "action": "train-ai"},
    )
    bus.publish(event)
    print(f"[publisher] Published event {i + 1}")


bus.close()