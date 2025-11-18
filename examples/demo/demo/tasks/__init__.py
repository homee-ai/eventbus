from eventbus.bus import EventName, EventHandlerWithBus, EventHandlerSimple

from .task_1 import web_crawler
from .task_2 import result

job_registry: dict[EventName, EventHandlerWithBus | EventHandlerSimple] = {
    "amazing_ai.crawler": web_crawler,
    "amazing_ai.result": result
}