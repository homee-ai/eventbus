import requests
import logging

from ..registry import register

from eventbus.models import Event
from eventbus.bus import BaseEventBus

logger = logging.getLogger(__name__)

@register("amazing_ai.crawler")
def web_crawler(bus: BaseEventBus, event: Event) -> None:
    url = event.detail.get("url")
    logger.info(f"Crawling {url}")
    output = requests.get(url).text
    bus.publish(Event(type="amazing_ai.result", detail={"url": url, "output": output}))
