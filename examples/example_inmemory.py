import time
import json
from queue import Queue
from eventbus.interfaces.registry import Registry
from eventbus.interfaces.listener import ListenerContract
from eventbus.interfaces.dispatcher import Dispatcher, DispatchConfig
from eventbus.config import build_eventbus


# ========= Step 1: define listener =========
class SubmitToMedium(ListenerContract):

    def handle(self, payload: bytes, context=None) -> None:
        print(f"[{self.name}]", json.loads(payload), context)


class ShareToFriend(ListenerContract):

    def handle(self, payload: bytes, context=None) -> None:
        print(f"[{self.name}]", json.loads(payload), context)


# ========= Step 2: setup Registry =========
event_to_listeners = {
    "finished_first_blog_post": [
        "SubmitToMedium",
        "ShareToFriend",
    ]
}
registry = Registry.new(
    event_to_listeners,
    [SubmitToMedium(), ShareToFriend()],
)
print(registry)

# ========= Step 3: init InMemory Backend =========
topics: dict[str, Queue] = {}
bus = build_eventbus(registry, backend="inmemory")
# ========= Step 4: start EventBus =========
bus.subscribe()
# ========= Step 5: build Dispatcher =========
dispatcher = Dispatcher(publisher=bus.publisher, registry=registry, cfg=DispatchConfig(topic="events"))
# publish event
payload = {"blog_id": 123, "medium_id": 456, "share_user_id": 789}
dispatcher.dispatch("finished_first_blog_post", payload, attributes={"priority": "normal"})
# ========= Step 6: waiting for thread =========
time.sleep(0.3)
# ========= Step 7: end =========
bus.close()
