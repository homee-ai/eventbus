import json, os, time
from eventbus.interfaces.registry import Registry
from eventbus.interfaces.listener import ListenerContract
from eventbus.interfaces.dispatcher import Dispatcher, DispatchConfig
from eventbus.config import build_eventbus

# ----------- define Listener -----------
class SubmitToMedium(ListenerContract):
    def name(self):
        return "submit_to_medium"
    def handle(self, payload: bytes, context=None):
        print(f"[{self.name}]", json.loads(payload), context)

class ShareToFriend(ListenerContract):
    def name(self):
        return "share_to_friend"
    def handle(self, payload: bytes, context=None):
        print(f"[{self.name}]", json.loads(payload), context)

# ----------- build Registry -----------
event_to_listeners = {
    "finished_first_blog_post": [
        "submit_to_medium",
        "share_to_friend",
    ]
}
registry = Registry.new(
    event_to_listeners,
    [SubmitToMedium(), ShareToFriend()],
)

# ----------- build Pub/Sub EventBus -----------
os.environ.setdefault("GCP_PROJECT_ID", "your-gcp-project")
os.environ.setdefault("EVENTBUS_TOPIC", "events")
os.environ.setdefault("EVENTBUS_SUBSCRIPTION", "events-sub.submit_to_medium")  # listener1 範例
bus = build_eventbus(registry, backend="pubsub")

# ----------- init subscribe -----------
bus.subscribe()

# ----------- build Dispatcher-----------
dispatcher = Dispatcher(publisher=bus.publisher, registry=registry, cfg=DispatchConfig(topic="events"))

payload = {"blog_id": 123, "medium_id": 456, "share_user_id": 789}
dispatcher.dispatch("finished_first_blog_post", payload, attributes={"priority": "normal"})

time.sleep(2)
bus.close()
