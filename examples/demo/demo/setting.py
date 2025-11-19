from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

#NOTE: It’s better to use a Pydantic dataclass instead of a standard dataclass, but considering the overall library dependencies, we use a regular dataclass here.
@dataclass
class Settings:
    environment: str
    log_level: str
    project_id: str
    topic_id: str
    subscription_id: str
    otlp_endpoint: str
    otlp_service_name: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        environment=os.getenv("ENVIRONMENT", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        project_id=os.getenv("GCP_PROJECT_ID"),
        topic_id=os.getenv("PUBSUB_TOPIC_NAME"),
        subscription_id=os.getenv("PUBSUB_SUBSCRIPTION_NAME"),
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
        otlp_service_name=os.getenv("OTLP_SERVICE_NAME"),
    )
