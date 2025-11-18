import logging

from eventbus.models import Event
from eventbus.bus import BaseEventBus

logger = logging.getLogger(__name__)


def result(bus: BaseEventBus, event: Event) -> None:
    url = event.detail.get("url")
    output = event.detail.get("output")
    logger.info(f"Origin URL: {url}")

    logger.info(f"Output Length: {len(output)}")
