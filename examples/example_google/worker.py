import time
import logging
import random
from eventbus.bus.google import PubSubEventBus
from eventbus import Event

logging.getLogger('PubSubEventBus').setLevel(logging.DEBUG)


def amazing_ai_job(event: Event):
    time.sleep(random.random())
    print("[worker] handling event:", event.model_dump())


with PubSubEventBus(
        project_id="housing-agent-463406",
        topic_name="test",
        prefix="ben-local"
) as bus:
    bus.subscribe({"example_a": amazing_ai_job})
    bus.run_forever()
