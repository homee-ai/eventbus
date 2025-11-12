# eventbus/backends/inmemory/queue_pub.py
from queue import Queue
from typing import Dict, Optional
from ...interfaces.base import Publisher

class InMemoryQueuePublisher(Publisher):
    def __init__(self, topics: Dict[str, Queue]):
        self.topics = topics

    def publish(self, topic: str, message: bytes, metadata: Optional[dict] = None) -> None:
        q = self.topics.setdefault(topic, Queue())
        q.put((message, metadata or {}))
