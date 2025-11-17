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


def setup_basic_logging(level: int = logging.INFO, fmt: Optional[str] = None) -> None:
    """Configure root logger with a default formatter including trace fields.

    Call once at application startup or before using eventbus if you want formatted output.
    """
    if fmt is None:
        fmt = "%(asctime)s %(levelname)s [trace_id=%(trace_id)s span_id=%(span_id)s] %(name)s - %(message)s"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(TraceContextFilter())

    root = logging.getLogger()
    # Avoid adding duplicate handlers if called multiple times
    already = any(isinstance(h, logging.StreamHandler) and isinstance(getattr(h, 'formatter', None), logging.Formatter) for h in root.handlers)
    if not already:
        root.addHandler(handler)
    root.setLevel(level)
