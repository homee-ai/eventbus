from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    environment: str
    log_level: str
    project_id: str
    topic_id: str
    subscription_id: str
    otlp_endpoint: str
    otlp_service_name: str
    idle_sleep: float = 0.3


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        environment=os.getenv("ENVIRONMENT"),
        log_level=os.getenv("LOG_LEVEL"),
        project_id=os.getenv("GCP_PROJECT_ID"),
        topic_id=os.getenv("PUBSUB_TOPIC_NAME"),
        subscription_id=os.getenv("PUBSUB_SUBSCRIPTION_NAME"),
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
        otlp_service_name=os.getenv("OTLP_SERVICE_NAME"),
    )
