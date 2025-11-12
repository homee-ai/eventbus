from typing import Iterable, Callable, Dict
from ...interfaces.base import EventBus
from ...interfaces.processor import Processor
from ...models import Event


class PubSubEventBus(EventBus):
    def __init__(self, publisher, subscriber, processor: Processor, topic: str = "undefined"):
        self.publisher = publisher
        self.subscriber = subscriber
        self.processor = processor
        self.topic = topic

    def publish(self, event: Event, attributes: Dict[str, str] | None = None) -> None:
        attrs = {"event_type": event.event_type, "priority": event.priority.value}
        if attributes:
            attrs.update(attributes)
        self.publisher.publish(self.topic, message=(event.detail and str(event.detail).encode("utf-8") or b"{}"),
                               metadata=attrs)

    def subscribe(self, event_types: Iterable[str] | None = None, handler: Callable[[Event], None] | None = None) -> None:
        def raw_handler(message: bytes, metadata: Dict[str, str]) -> None:
            self.processor.process(message, metadata)

        self.subscriber.subscribe(self.topic, raw_handler)

    def close(self) -> None:
        self.subscriber.stop()
