import contextvars
import uuid
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any, Iterator
from .models import Event

from opentelemetry import trace as _otel_trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import (
    SpanContext as _SpanContext,
    TraceFlags as _TraceFlags,
    TraceState as _TraceState,
    set_span_in_context as _set_span_in_context,
)
_OTEL_AVAILABLE = True

# Context variables to store tracing information per logical context (task/thread)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
_span_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("span_id", default=None)

# Module-level OTel tracer (optional)
_TRACER = None


def _gen_id() -> str:
    return uuid.uuid4().hex


def _gen_trace_id() -> str:
    """Generate a 32-hex-character trace_id (128-bit)"""
    return uuid.uuid4().hex  # 32 hex chars


def _gen_span_id() -> str:
    """Generate a 16-hex-character span_id (64-bit). Use lower 64 bits of UUID4."""
    # uuid4 is 128-bit (32 hex). Take last 16 hex chars to simulate 64-bit id.
    return uuid.uuid4().hex[-16:]


def _hex_id(n: int, length: int) -> str:
    return f"{n:0{length}x}"


def _int_from_hex(s: str) -> Optional[int]:
    try:
        return int(s, 16)
    except Exception:
        return None


def setup_tracing(
    otlp_endpoint: Optional[str] = None,
    *,
    service_name: str = "eventbus",
    headers: Optional[Dict[str, str]] = None
) -> bool:
    """Optionally configure OpenTelemetry to export spans to an OTLP collector.

    - Returns True if OpenTelemetry is available and configured; False otherwise.
    - This function is safe to call multiple times; subsequent calls replace previous config.

    Example:
        setup_tracing(
            otlp_endpoint="http://localhost:4318/v1/traces",
            service_name="eventbus-demo")
    """
    global _TRACER
    if not _OTEL_AVAILABLE:
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers or {}
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    _otel_trace.set_tracer_provider(provider)
    _TRACER = _otel_trace.get_tracer(__name__)
    return True


def shutdown_tracing() -> None:
    """Flush and shutdown OpenTelemetry provider if configured."""
    if _OTEL_AVAILABLE:
        provider = _otel_trace.get_tracer_provider()  # type: ignore
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()  # type: ignore[misc]
            except Exception:
                pass


def get_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """Return current (trace_id, span_id) from context.

    If OpenTelemetry is active, prefer its current span context.
    """
    if _OTEL_AVAILABLE:
        try:
            span = _otel_trace.get_current_span()
            # InvalidSpan for no-op provider; valid spans have context with non-zero ids
            ctx = span.get_span_context()
            # Protect against InvalidSpan or invalid context
            if getattr(span, "is_recording", lambda: False)() or (getattr(ctx, "trace_id", 0) or getattr(ctx, "span_id", 0)):
                trace_hex = _hex_id(ctx.trace_id, 32) if getattr(ctx, "trace_id", 0) else None
                span_hex = _hex_id(ctx.span_id, 16) if getattr(ctx, "span_id", 0) else None
                if trace_hex or span_hex:
                    return trace_hex, span_hex
        except Exception:
            pass
    return _trace_id_var.get(), _span_id_var.get()


def set_trace_ids(trace_id: Optional[str], span_id: Optional[str]) -> None:
    """Set current trace_id and span_id in context (local contextvars only)."""
    _trace_id_var.set(trace_id)
    _span_id_var.set(span_id)


def ensure_trace() -> Tuple[str, str]:
    """Ensure there is a trace in the context, create if missing. Returns (trace_id, span_id)."""
    trace_id, span_id = get_trace_ids()
    if trace_id is None:
        trace_id = _gen_trace_id()
    if span_id is None:
        span_id = _gen_span_id()
    set_trace_ids(trace_id, span_id)
    return trace_id, span_id


def _build_parent_context(trace_id_hex: Optional[str], span_id_hex: Optional[str]):
    """Build an OpenTelemetry parent context from given hex ids if possible."""
    if not (_OTEL_AVAILABLE and trace_id_hex and span_id_hex):
        return None
    trace_int = _int_from_hex(trace_id_hex)
    span_int = _int_from_hex(span_id_hex)
    if not trace_int or not span_int:
        return None
    try:
        parent_ctx = _SpanContext(
            trace_id=trace_int,
            span_id=span_int,
            is_remote=True,
            trace_flags=_TraceFlags(_TraceFlags.SAMPLED),
            trace_state=_TraceState(),
        )
        # Create a non-recording span with this context
        parent_span = _otel_trace.NonRecordingSpan(parent_ctx)  # type: ignore[attr-defined]
        return _set_span_in_context(parent_span)
    except Exception:
        return None


@contextmanager
def start_span(
    name: str = "span",
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
) -> Iterator[Tuple[str, str]]:
    """Context manager to start a new span.

    - If OpenTelemetry is configured, an OTel span is created and set as current.
    - If trace_id/parent_span_id are provided, they are used as the parent context when possible.
    - Our local contextvars are always synchronized so logs show trace_id/span_id.

    Yields (trace_id, span_id).
    """
    current_trace, current_span = get_trace_ids()

    # If no explicit trace provided, try to reuse current from local context
    base_trace = trace_id or current_trace
    base_span = parent_span_id or current_span

    # Start OTel span if available
    if _OTEL_AVAILABLE and _TRACER is not None:
        ctx = _build_parent_context(base_trace, base_span)
        cm = _TRACER.start_as_current_span(name, context=ctx)
        with cm as span:
            try:
                ctx2 = span.get_span_context()
                this_trace = _hex_id(ctx2.trace_id, 32)
                this_span = _hex_id(ctx2.span_id, 16)
                token_trace = _trace_id_var.set(this_trace)
                token_span = _span_id_var.set(this_span)
                yield this_trace, this_span
            finally:
                _trace_id_var.reset(token_trace)
                _span_id_var.reset(token_span)
        return

    # Fallback: local contextvars only
    use_trace = base_trace or _gen_id()
    new_span_id = _gen_id()
    token_trace = _trace_id_var.set(use_trace)
    token_span = _span_id_var.set(new_span_id)
    try:
        yield use_trace, new_span_id
    finally:
        _trace_id_var.reset(token_trace)
        _span_id_var.reset(token_span)


def inject_trace_to_event(event: Event, new_trace: bool = False) -> Event:
    """Ensure event.metadata contains trace information.
    - If event.metadata already contains a trace.trace_id, ALWAYS keep using it and sync context to it.
    - If new_trace=True and no existing trace_id on the event, create a fresh (trace_id, span_id) and set context.
    - Else, reuse the current context (creating if missing).
    Modifies event in-place.
    """
    # Read any existing trace info on the event
    trace_meta = event.metadata.get("trace") or {}
    existing_trace_id = trace_meta.get("trace_id")
    existing_span_id = trace_meta.get("span_id")

    final_trace_id: Optional[str]
    final_span_id: Optional[str]

    if existing_trace_id:
        # Respect existing trace_id from the event and keep using it
        # If span_id missing, generate one (or reuse current if present)
        current_trace, current_span = get_trace_ids()
        final_trace_id = existing_trace_id
        final_span_id = existing_span_id or current_span or _gen_span_id()
        set_trace_ids(final_trace_id, final_span_id)
    else:
        if new_trace:
            # Force new trace for publish action when event didn't carry a trace
            set_trace_ids(_gen_trace_id(), _gen_span_id())
        # Ensure context has ids
        final_trace_id, final_span_id = ensure_trace()

    # Update event metadata trace, preserving other custom fields if any
    trace_meta.update({"trace_id": final_trace_id, "span_id": final_span_id})
    event.metadata["trace"] = trace_meta
    return event


def extract_trace_from_event(event: Event) -> Tuple[Optional[str], Optional[str]]:
    """Extract trace info from event.metadata and set it into the local context.
    Returns (trace_id, span_id) that were found (or (None, None)).
    """
    trace_meta = event.metadata.get("trace") if hasattr(event, "metadata") else None

    if isinstance(trace_meta, dict):
        trace_id_val = trace_meta.get("trace_id")
        span_id_val = trace_meta.get("span_id")
        set_trace_ids(trace_id_val, span_id_val)
        return trace_id_val, span_id_val
    return None, None


def get_trace_fields_for_log() -> Dict[str, Any]:
    """Return a dict with trace_id and span_id for logging enrichment.

    If OpenTelemetry is active and a span is current, prefer its IDs.
    """
    trace_id_val, span_id_val = get_trace_ids()
    return {
        "trace_id": trace_id_val or "-",
        "span_id": span_id_val or "-",
    }
