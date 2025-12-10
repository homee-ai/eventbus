from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    environment: str
    enable_filter_attributes: bool = False
    log_level: str
    gcp_project_id: str
    pubsub_topic_name: str
    pubsub_dlq_topic_name: str = ""
    pubsub_subscription_name: str
    pubsub_dlq_subscription_name: str = ""
    otlp_endpoint: str
    otlp_service_name: str
    eventbus_tasks_packages: str | None = None
