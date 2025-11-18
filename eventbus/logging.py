import os
from typing import Any, Dict
import logging
from pythonjsonlogger import json
from opentelemetry import trace


class OTELTraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span is not None else None

        if span_ctx and span_ctx.is_valid:
            record.trace_id = format(span_ctx.trace_id, "032x")
            record.span_id = format(span_ctx.span_id, "016x")
        else:
            record.trace_id = "-"
            record.span_id = "-"
        return True


class HomeeNestedJsonFormatter(json.JsonFormatter):
    def process_log_record(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        asctime = log_record.pop("asctime", None)
        level = log_record.pop("levelname", None)
        logger_name = log_record.pop("name", None)
        message = log_record.pop("message", None)
        pathname = log_record.pop("pathname", None)
        lineno = log_record.pop("lineno", None)
        trace_id = log_record.pop("trace_id", None)
        span_id = log_record.pop("span_id", None)

        nested = {
            "asctime": asctime,
            "level": level,
            "logger": logger_name,
            "message": message,
            "extra": log_record,
            "detail": {
                "pathname": pathname,
                "lineno": lineno,
                "trace_id": trace_id,
                "span_id": span_id,
            },
        }
        return nested


_env = (os.getenv("ENVIRONMENT") or "").lower()
_IS_LOCAL = _env in {"local"}

# Choose a formatter name dynamically
_formatter_name = "text" if _IS_LOCAL else "json"

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "otel_trace": {"()": OTELTraceFilter},
    },
    "formatters": {
        # JSON formatter for non-local environments
        "json": {
            "()": HomeeNestedJsonFormatter,
            "format": "%(asctime) %(name) %(pathname)s %(lineno)d %(levelname)s %(message)s %(trace_id)s %(span_id)s",
            "json_ensure_ascii": False,
        },
        # Plain text formatter for local
        "text": {
            "()": "logging.Formatter",
            "format": "%(levelname)s | %(name)s | %(message)s | trace_id=%(trace_id)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": _formatter_name,
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["otel_trace"],
        },
    },
    "loggers": {
        # default log setting
        "": {
            "handlers": ["default"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}
