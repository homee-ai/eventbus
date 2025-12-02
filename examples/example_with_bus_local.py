import time
import logging
from eventbus import Event, EventPriority
from eventbus.bus.local import LocalEventBus

logging.getLogger('LocalEventBus').setLevel(logging.DEBUG)
logger = logging.getLogger('Runtime')


def amazing_ai_job(local_bus: LocalEventBus, event: Event):
    logging.getLogger('amazing_ai_job').info("[handler]", extra=event.model_dump())
    time.sleep(10)
    local_bus.publish(Event(type="test_b", priority=EventPriority.HIGH, detail={"job_id": 123}))


def second_job(event: Event):
    logging.getLogger('second_job').info("[handler]", extra=event.model_dump())


bus = LocalEventBus()
bus.subscribe({"test_a": amazing_ai_job})
bus.subscribe({"test_b": second_job})
bus.publish(Event(type="test_a", priority=EventPriority.HIGH, detail={"job_id": 123}))
logger.info("Waiting for events...")
bus.consume()
logger.info("Events consumed.")
bus.close()
logger.info("Bus closed.")
