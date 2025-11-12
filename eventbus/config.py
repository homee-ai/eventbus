# eventbus/config.py
import os
from queue import Queue
from .interfaces.processor import Processor
from .interfaces.registry import Registry
from .backends.inmemory.queue_pub import InMemoryQueuePublisher
from .backends.inmemory.queue_sub import InMemoryQueueSubscriber
from .backends.inmemory.bus import InMemoryEventBus
from .backends.pubsub.pub import PubSubPublisher
from .backends.pubsub.sub import PubSubSubscriber
from .backends.pubsub.bus import PubSubEventBus


def build_eventbus(registry: Registry, backend: str = None):
    backend = backend or os.getenv("EVENTBUS_BACKEND", "pubsub")

    if backend == "inmemory":
        topics: dict[str, Queue] = {}
        pub = InMemoryQueuePublisher(topics)
        sub = InMemoryQueueSubscriber(topics)
        return InMemoryEventBus(pub, sub, Processor(registry), topic="events")

    elif backend == "pubsub":
        project = os.getenv("GCP_PROJECT_ID", "your-project")
        topic_id = os.getenv("EVENTBUS_TOPIC", "events")
        sub_id = os.getenv("EVENTBUS_SUBSCRIPTION", "events-sub.example_a")  # 每個 listener/event_type 一個 sub
        pub = PubSubPublisher(project, topic_id)
        sub = PubSubSubscriber(project, sub_id)
        return PubSubEventBus(pub, sub, Processor(registry), topic="events")

    else:
        raise ValueError(f"unknown backend: {backend}")
