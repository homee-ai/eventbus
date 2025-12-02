import logging
from core import Event, EventPriority
from core.bus.local import LocalEventBus


logging.getLogger('LocalEventBus').setLevel(logging.DEBUG)

def amazing_ai_job(event: Event):
    logger = logging.getLogger('amazing_ai_job')
    logger.info("[handler]", extra=event.model_dump())

bus = LocalEventBus()

bus.subscribe({"test_a": amazing_ai_job})
bus.publish(Event(type="test_a", priority=EventPriority.HIGH, detail={"job_id": 123}))
bus.publish(Event(type="test_b", priority=EventPriority.HIGH, detail={"job_id": 123}))
bus.consume()
bus.close()