import time
from queue import Queue, Empty
from typing import Dict
from ...interfaces.base import Subscriber, MessageHandler


class InMemoryQueueSubscriber(Subscriber):
    def __init__(self, topics: Dict[str, Queue]):
        self.topics = topics
        self.handlers: Dict[str, MessageHandler] = {}
        self._running = False

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self.handlers[topic] = handler
        self.topics.setdefault(topic, Queue())

    def run(self) -> None:
        self._running = True
        while self._running:
            idle = True
            for topic, q in list(self.topics.items()):
                handler = self.handlers.get(topic)
                if not handler:
                    continue
                try:
                    msg, meta = q.get(timeout=0.05)
                    idle = False
                    try:
                        handler(msg, meta or {})
                    finally:
                        q.task_done()
                except Empty:
                    pass
            if idle:
                time.sleep(0.02)

    def stop(self) -> None:
        self._running = False
