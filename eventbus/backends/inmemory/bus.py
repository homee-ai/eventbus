# eventbus/backends/inmemory/bus.py
import threading
from ...interfaces.base import EventBus
from ...interfaces.processor import Processor
from ...interfaces.base import Publisher, Subscriber
from ...models import Event
from typing import Iterable, Callable, Dict

class InMemoryEventBus(EventBus):
    def __init__(self, publisher: Publisher, subscriber: Subscriber, processor: Processor, topic: str = "events"):
        self.publisher = publisher
        self.subscriber = subscriber
        self.processor = processor
        self.topic = topic
        self._th: threading.Thread | None = None

    def publish(self, event: Event, attributes: Dict[str, str] | None = None) -> None:
        attrs = {"event_type": event.event_type, "priority": event.priority.value}
        if attributes:
            attrs.update(attributes)
        self.publisher.publish(self.topic, event.detail and str(event.detail).encode("utf-8") or b"{}", attrs)

    def subscribe(self, event_types: Iterable[str] | None = None, handler: Callable[[Event], None] | None = None) -> None:
        def raw_handler(message: bytes, metadata: Dict[str, str]) -> None:
            self.processor.process(message, metadata)

        self.subscriber.subscribe(self.topic, raw_handler)

        self._th = threading.Thread(target=self.subscriber.run, daemon=True)
        self._th.start()

    def close(self) -> None:
        self.subscriber.stop()
        if self._th:
            self._th.join(timeout=1.0)
