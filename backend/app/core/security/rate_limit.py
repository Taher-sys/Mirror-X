"""Sliding window in-memory rate limiting middleware."""

import time
from collections import defaultdict
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings


class SlidingWindowRateLimiter:
    """Sliding-window counter for rate limiting client requests."""

    def __init__(self, limit_per_minute: int = 120) -> None:
        self.limit = limit_per_minute
        # client_key -> list of timestamps
        self.windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_key: str, cost: int = 1) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, retry_after_seconds)."""
        now = time.time()
        cutoff = now - 60.0

        # Purge timestamps older than 60s
        timestamps = [t for t in self.windows[client_key] if t > cutoff]
        self.windows[client_key] = timestamps

        current_count = len(timestamps)
        if current_count + cost > self.limit:
            oldest = timestamps[0] if timestamps else now
            retry_after = max(1, int(60.0 - (now - oldest)))
            return False, 0, retry_after

        # Record this request
        for _ in range(cost):
            timestamps.append(now)
        self.windows[client_key] = timestamps
        remaining = max(0, self.limit - len(timestamps))
        return True, remaining, 0

    def reset(self) -> None:
        """Clear all active client windows."""
        self.windows.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware enforcing per-client request quotas."""

    def __init__(
        self,
        app: Any,
        default_limit: int = 120,
        sensitive_limit: int = 30,
        exempt_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.default_limiter = SlidingWindowRateLimiter(limit_per_minute=default_limit)
        self.sensitive_limiter = SlidingWindowRateLimiter(limit_per_minute=sensitive_limit)
        self.exempt_paths = exempt_paths or {
            "/api/v1/health",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        settings = get_settings()
        if not getattr(settings, "rate_limit_enabled", True):
            return await call_next(request)

        path = request.url.path
        # Skip exempt endpoints
        if path in self.exempt_paths or any(path.startswith(p) for p in ("/docs", "/redoc")):
            return await call_next(request)

        # Extract client identifier: X-Forwarded-For or client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Apply tighter limits to expensive routes
        is_sensitive = any(sensitive in path for sensitive in ("/ingest", "/scenarios/generate", "/ai/dataset"))
        limiter = self.sensitive_limiter if is_sensitive else self.default_limiter

        allowed, remaining, retry_after = limiter.is_allowed(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "status": "error",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "details": [{"retry_after": retry_after, "limit": limiter.limit}],
                    },
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
