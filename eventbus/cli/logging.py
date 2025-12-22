import logging.config as setup_logging
from eventbus.logging import LOGGING_CONFIG
from pydantic import ValidationError

from .setting import Settings


def format_settings_error(error: ValidationError) -> str:
    """
    Turn a Pydantic ValidationError into a short, user-friendly message.
    """
    missing_fields: list[str] = []

    for err in error.errors():
        # err example: {'type': 'missing', 'loc': ('gcp_project_id',), ...}
        if err.get("type") == "missing" and err.get("loc"):
            field = str(err["loc"][0])
            missing_fields.append(field)

    if missing_fields:
        env_vars = [field.upper() for field in missing_fields]
        return (
            "Missing required environment variables:\n"
            f"  Fields: {', '.join(sorted(missing_fields))}\n"
            f"  Env vars: {', '.join(sorted(env_vars))}\n"
            "Please set them in your environment or .env file and retry."
        )

    # fallback: still keep it short
    return f"Invalid settings: {error}"


def setup_logging_config():
    setting = Settings()
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
