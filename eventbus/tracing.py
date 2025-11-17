import contextvars
import uuid
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any, Iterator
from .models import Event

# Context variables to store tracing information per logical context (task/thread)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
_span_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("span_id", default=None)


def _gen_id() -> str:
    return uuid.uuid4().hex


def get_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """Return current (trace_id, span_id) from context."""
    return _trace_id_var.get(), _span_id_var.get()


def set_trace_ids(trace_id: Optional[str], span_id: Optional[str]) -> None:
    """Set current trace_id and span_id in context."""
    _trace_id_var.set(trace_id)
    _span_id_var.set(span_id)


def ensure_trace() -> Tuple[str, str]:
    """Ensure there is a trace in the context, create if missing. Returns (trace_id, span_id)."""
    trace_id, span_id = get_trace_ids()
    if trace_id is None:
        trace_id = _gen_id()
    if span_id is None:
        span_id = _gen_id()
    set_trace_ids(trace_id, span_id)
    return trace_id, span_id


@contextmanager
def start_span(name: str = "span", trace_id: Optional[str] = None, parent_span_id: Optional[str] = None) -> Iterator[Tuple[str, str]]:
    """Context manager to start a new span.

    - If trace_id is provided, use it; else reuse current or create a new one.
    - If parent_span_id is provided, use it as parent and create a child span id.
      Otherwise, reuse current trace and create a new span id.
    Yields (trace_id, span_id).
    """
    current_trace, current_span = get_trace_ids()

    if trace_id is None:
        trace_id = current_trace or _gen_id()
    # Parent is either provided or current span
    parent_span_id = parent_span_id or current_span

    new_span_id = _gen_id()
    token_trace = _trace_id_var.set(trace_id)
    token_span = _span_id_var.set(new_span_id)
    try:
        yield trace_id, new_span_id
    finally:
        # restore previous context
        _trace_id_var.reset(token_trace)
        _span_id_var.reset(token_span)


def inject_trace_to_event(event: Event, new_trace: bool = False) -> None:
    """Ensure event.metadata contains trace information.
    - If new_trace=True, create a fresh trace_id/span_id and set it into context first.
    - Else, reuse current context (creating if missing).
    Modifies event in-place.
    """
    if new_trace:
        # Force new trace for publish action
        set_trace_ids(_gen_id(), _gen_id())
    trace_id, span_id = ensure_trace()
    trace_meta = event.metadata.get("trace") or {}
    trace_meta.update({"trace_id": trace_id, "span_id": span_id})
    event.metadata["trace"] = trace_meta


def extract_trace_from_event(event: Event) -> Tuple[Optional[str], Optional[str]]:
    """Extract trace info from event.metadata and set it into the current context.
    Returns (trace_id, span_id) that were found (or (None, None)).
    """
    trace_meta = event.metadata.get("trace") if hasattr(event, "metadata") else None
    if isinstance(trace_meta, dict):
        trace_id = trace_meta.get("trace_id")
        span_id = trace_meta.get("span_id")
        set_trace_ids(trace_id, span_id)
        return trace_id, span_id
    return None, None


def get_trace_fields_for_log() -> Dict[str, Any]:
    """Return a dict with trace_id and span_id for logging enrichment."""
    trace_id, span_id = get_trace_ids()
    return {
        "trace_id": trace_id or "-",
        "span_id": span_id or "-",
    }
