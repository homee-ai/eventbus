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
        topic_name="ben-local-test",
        # give each worker its own subscription name
        subscription_name="ben-local-test-sub-example-a",
        # only receive events with type==example_a
        filter_types=["example_a"],
) as bus:
    bus.subscribe({"example_a": amazing_ai_job})
    bus.run_forever()
