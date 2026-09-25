"""OpenTelemetry-compatible tracing infrastructure with secret-safe context propagation."""

import functools
import inspect
import time
import uuid
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from app.core.security.sanitizer import sanitize_secrets

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class SpanEvent:
    """An event/log timestamped within a Span."""

    name: str
    timestamp: float
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """OpenTelemetry-compliant Span structure."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    status: str = "OK"  # "OK" or "ERROR"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)
    error_message: str | None = None

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a single sanitized attribute on this span."""
        self.attributes[key] = sanitize_secrets(value)

    def set_attributes(self, attrs: dict[str, Any]) -> None:
        """Merge a dictionary of sanitized attributes into this span."""
        for k, v in attrs.items():
            self.set_attribute(k, v)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add a timestamped event to this span."""
        sanitized_attrs = sanitize_secrets(attributes or {})
        self.events.append(SpanEvent(name=name, timestamp=time.time(), attributes=sanitized_attrs))

    def record_exception(self, exc: Exception) -> None:
        """Record an exception on this span."""
        self.status = "ERROR"
        self.error_message = sanitize_secrets(str(exc))
        self.add_event(
            "exception",
            {
                "exception.type": exc.__class__.__name__,
                "exception.message": self.error_message,
            },
        )

    def finish(self, status: str | None = None) -> None:
        """Close span and record elapsed duration."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 3)
            if status:
                self.status = status

    def to_dict(self) -> dict[str, Any]:
        """Serialize span to dictionary safely."""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": sanitize_secrets(self.attributes),
            "events": [
                {
                    "name": e.name,
                    "timestamp": e.timestamp,
                    "attributes": sanitize_secrets(e.attributes),
                }
                for e in self.events
            ],
            "error_message": self.error_message,
        }


# ContextVar holding the currently active Span in the current execution context
_CURRENT_SPAN: ContextVar[Span | None] = ContextVar("mirrorx_current_span", default=None)


class SpanContextManager:
    """Context manager for managing span lifecycle in sync and async contexts."""

    def __init__(self, span: Span, tracer: "Tracer") -> None:
        self.span = span
        self.tracer = tracer
        self._token = None

    def __enter__(self) -> Span:
        self._token = _CURRENT_SPAN.set(self.span)
        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_val is not None:
                self.span.record_exception(exc_val)
            self.span.finish()
            self.tracer.record_completed_span(self.span)
        finally:
            if self._token is not None:
                _CURRENT_SPAN.reset(self._token)

    async def __aenter__(self) -> Span:
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


class Tracer:
    """OpenTelemetry-compatible Tracer managing span creation, propagation, and memory buffer."""

    def __init__(self, max_buffer_size: int = 1000) -> None:
        self.max_buffer_size = max_buffer_size
        self._span_buffer: deque[Span] = deque(maxlen=max_buffer_size)

    def get_current_span(self) -> Span | None:
        """Return the currently active span in this async context."""
        return _CURRENT_SPAN.get()

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        parent_span_id: str | None = None,
        trace_id: str | None = None,
    ) -> SpanContextManager:
        """Start a new span as a child of the current span or specified parent."""
        current = self.get_current_span()

        resolved_trace_id = trace_id or (current.trace_id if current else uuid.uuid4().hex)
        resolved_parent_id = parent_span_id or (current.span_id if current else None)
        span_id = uuid.uuid4().hex[:16]

        span = Span(
            name=name,
            trace_id=resolved_trace_id,
            span_id=span_id,
            parent_span_id=resolved_parent_id,
            attributes=sanitize_secrets(attributes or {}),
        )
        return SpanContextManager(span, self)

    def start_as_current_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> SpanContextManager:
        """Convenience alias for start_span."""
        return self.start_span(name, attributes)

    def record_completed_span(self, span: Span) -> None:
        """Store finished span in ring buffer."""
        self._span_buffer.append(span)

    def get_recent_spans(
        self,
        limit: int = 100,
        trace_id: str | None = None,
        name: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve recent spans matching filter criteria."""
        spans = list(self._span_buffer)
        if trace_id:
            spans = [s for s in spans if s.trace_id == trace_id]
        if name:
            spans = [s for s in spans if name.lower() in s.name.lower()]
        if status:
            spans = [s for s in spans if s.status.upper() == status.upper()]

        # Return latest spans first up to limit
        return [s.to_dict() for s in reversed(spans)][:limit]

    def get_telemetry_summary(self) -> dict[str, Any]:
        """Calculate aggregate telemetry metrics across recorded spans."""
        spans = list(self._span_buffer)
        total = len(spans)
        if total == 0:
            return {
                "total_spans": 0,
                "error_spans": 0,
                "error_rate": 0.0,
                "avg_duration_ms": 0.0,
                "p95_duration_ms": 0.0,
                "components": {},
            }

        errors = sum(1 for s in spans if s.status == "ERROR")
        durations = sorted(s.duration_ms for s in spans)
        avg_dur = round(sum(durations) / total, 2)
        p95_idx = int(0.95 * total)
        p95_dur = round(durations[min(p95_idx, total - 1)], 2)

        # Group by top-level component prefix (e.g. 'http', 'ingestion', 'trust')
        components: dict[str, int] = {}
        for s in spans:
            comp = s.name.split(".")[0].split(" ")[0].lower()
            components[comp] = components.get(comp, 0) + 1

        return {
            "total_spans": total,
            "error_spans": errors,
            "error_rate": round(errors / total, 4),
            "avg_duration_ms": avg_dur,
            "p95_duration_ms": p95_dur,
            "components": components,
        }

    def clear(self) -> None:
        """Clear memory buffer."""
        self._span_buffer.clear()


# Global Singleton Tracer instance
_GLOBAL_TRACER = Tracer()


def get_tracer() -> Tracer:
    """Access the global Tracer instance."""
    return _GLOBAL_TRACER


def trace_span(span_name: str, attributes: dict[str, Any] | None = None) -> Callable[[F], F]:
    """Decorator to automatically trace a function or coroutine execution."""

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer()
                with tracer.start_span(span_name, attributes=attributes) as span:
                    span.set_attribute("code.function", func.__name__)
                    span.set_attribute("code.module", func.__module__)
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer()
                with tracer.start_span(span_name, attributes=attributes) as span:
                    span.set_attribute("code.function", func.__name__)
                    span.set_attribute("code.module", func.__module__)
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore

    return decorator
