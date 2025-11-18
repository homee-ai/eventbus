import os
import logging.config as setup_logging
from dotenv import load_dotenv
from eventbus.logging import LOGGING_CONFIG

from .setting import load_settings
load_dotenv()

def setup_logging_config():
    setting = load_settings()
    """Setup logging configuration after .env is loaded"""
    # Import here to avoid circular dependency and ensure .env is loaded first

    # Force reload the environment variables
    env = setting.environment.lower()
    log_level = setting.log_level.upper()

    # Update the config with current environment values
    LOGGING_CONFIG["loggers"][""]["level"] = log_level

    # Update formatter based on environment
    is_local = env in {"local"}
    formatter_name = "text" if is_local else "json"
    LOGGING_CONFIG["handlers"]["default"]["formatter"] = formatter_name

    setup_logging.dictConfig(LOGGING_CONFIG)