import json
import logging
from typing import Optional
from .tracing import get_trace_fields_for_log


class TraceContextFilter(logging.Filter):
    """Logging filter that injects trace_id and span_id into LogRecord."""
    def filter(self, record: logging.LogRecord) -> bool:
        fields = get_trace_fields_for_log()
        # Attach as attributes to be used in Formatter
        setattr(record, "trace_id", fields["trace_id"])  # type: ignore[attr-defined]
        setattr(record, "span_id", fields["span_id"])    # type: ignore[attr-defined]
        return True


# Standard attributes present on LogRecord; anything else is considered "extra"
_STANDARD_RECORD_ATTRS = {
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module',
    'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs',
    'relativeCreated', 'thread', 'threadName', 'processName', 'process', 'message',
    'asctime', 'taskName'
}


class EnhancedFormatter(logging.Formatter):
    """Formatter that appends any logging `extra` fields as JSON at the end.

    Trace fields (trace_id/span_id) are excluded because they already appear in the prefix.
    """
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        # Collect extras: keys not in standard set and not our trace fields
        extras = {}
        for k, v in record.__dict__.items():
            if k in _STANDARD_RECORD_ATTRS:
                continue
            if k in ("trace_id", "span_id"):
                continue
            # Private/internal attributes are ignored
            if k.startswith('_'):
                continue
            extras[k] = v
        if extras:
            try:
                extra_json = json.dumps(extras, ensure_ascii=False, default=str, sort_keys=True)
            except Exception:
                # Fallback to str() if serialization fails
                extra_json = str(extras)
            return f"{base} {extra_json}"
        return base


def setup_basic_logging(level: int = logging.INFO, fmt: Optional[str] = None) -> None:
    """Configure root logger with a default formatter including trace fields and extras.

    Call once at application startup or before using eventbus if you want formatted output.
    """
    if fmt is None:
        fmt = "%(asctime)s %(levelname)s [trace_id=%(trace_id)s span_id=%(span_id)s] %(name)s - %(message)s"

    handler = logging.StreamHandler()
    handler.setFormatter(EnhancedFormatter(fmt))
    handler.addFilter(TraceContextFilter())

    root = logging.getLogger()
    # Avoid adding duplicate handlers if called multiple times
    already = any(isinstance(h, logging.StreamHandler) and isinstance(getattr(h, 'formatter', None), logging.Formatter) for h in root.handlers)
    if not already:
        root.addHandler(handler)
    root.setLevel(level)
