from typing import Optional, Dict
from google.cloud import pubsub_v1
from ...interfaces.base import Publisher


class PubSubPublisher(Publisher):
    def __init__(self, project_id: str, topic_id: str):
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(project_id, topic_id)

    def publish(self, topic: str, message: bytes, metadata: Optional[Dict[str, str]] = None) -> None:
        attrs = metadata or {}
        self._publisher.publish(self._topic_path, data=message, **attrs).result()
