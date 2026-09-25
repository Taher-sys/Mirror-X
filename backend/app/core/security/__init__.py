"""Security, RBAC, Sandboxing, and Protection module."""

from app.core.security.auth import (
    Role,
    UserPrincipal,
    get_current_principal,
    require_permission,
    require_role,
)
from app.core.security.rate_limit import RateLimitMiddleware, SlidingWindowRateLimiter
from app.core.security.sandbox import IngestionSandboxViolation, validate_ingestion_payload
from app.core.security.sanitizer import (
    is_safe_relative_path,
    sanitize_filename,
    sanitize_secrets,
)

__all__ = [
    "Role",
    "UserPrincipal",
    "get_current_principal",
    "require_role",
    "require_permission",
    "RateLimitMiddleware",
    "SlidingWindowRateLimiter",
    "validate_ingestion_payload",
    "IngestionSandboxViolation",
    "sanitize_secrets",
    "is_safe_relative_path",
    "sanitize_filename",
]
