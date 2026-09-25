"""Observability and W3C Trace Context HTTP middleware."""

import re
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.observability.tracer import get_tracer
from app.core.security.sanitizer import sanitize_secrets

# W3C TraceContext traceparent regex: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
W3C_TRACEPARENT_PATTERN = re.compile(r"^00-([a-fA-F0-9]{32})-([a-fA-F0-9]{16})-[a-fA-F0-9]{2}$")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware to trace all incoming HTTP requests according to W3C Trace Context."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.tracer = get_tracer()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        traceparent = request.headers.get("traceparent")
        incoming_trace_id: str | None = None
        incoming_parent_span_id: str | None = None

        if traceparent:
            match = W3C_TRACEPARENT_PATTERN.match(traceparent.strip())
            if match:
                incoming_trace_id = match.group(1).lower()
                incoming_parent_span_id = match.group(2).lower()

        # Fallback to X-Trace-ID header if present
        if not incoming_trace_id:
            custom_trace_id = request.headers.get("X-Trace-ID")
            if custom_trace_id and len(custom_trace_id) == 32:
                incoming_trace_id = custom_trace_id.lower()

        span_name = f"HTTP {request.method} {request.url.path}"
        span_mgr = self.tracer.start_span(
            name=span_name,
            trace_id=incoming_trace_id,
            parent_span_id=incoming_parent_span_id,
        )

        with span_mgr as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.target", request.url.path)
            span.set_attribute("http.client_ip", request.client.host if request.client else "unknown")

            # Redact and attach safe query parameters
            query_params = dict(request.query_params)
            if query_params:
                span.set_attribute("http.query_params", sanitize_secrets(query_params))

            try:
                response: Response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                if response.status_code >= 500:
                    span.status = "ERROR"

                # Propagate trace identifiers back to the caller
                response.headers["X-Trace-ID"] = span.trace_id
                response.headers["X-Span-ID"] = span.span_id
                response.headers["traceparent"] = f"00-{span.trace_id}-{span.span_id}-01"
                return response
            except Exception as exc:
                span.record_exception(exc)
                raise
