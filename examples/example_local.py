from eventbus import Event, EventPriority
from eventbus.bus.local import LocalEventBus


def amazing_ai_job(event: Event):
    print("[handler]", event.model_dump())


bus = LocalEventBus()

bus.subscribe({"test_a": amazing_ai_job})
bus.publish(Event(type="test_a", priority=EventPriority.HIGH, detail={"job_id": 123}))
bus.publish(Event(type="test_b", priority=EventPriority.HIGH, detail={"job_id": 123}))
bus.consume()
bus.close()
