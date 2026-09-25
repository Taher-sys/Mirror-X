"""Security and Cryptographic Verification for the Edge Runtime.

Enforces HMAC-SHA256 snapshot signing, sync token authentication, and credential sanitization
to treat edge devices as constrained, less-trusted nodes.
"""

import hashlib
import hmac
import json
import os
from typing import Any


DEFAULT_SYNC_SECRET = os.environ.get("MIRRORX_EDGE_SYNC_SECRET", "mirrorx-edge-auth-secret-v1")


def sign_snapshot_payload(payload: dict[str, Any], secret: str = DEFAULT_SYNC_SECRET) -> str:
    """Generate an HMAC-SHA256 signature for a cloud snapshot payload."""
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), serialized, hashlib.sha256).hexdigest()
    return signature


def verify_snapshot_signature(payload: dict[str, Any], signature: str, secret: str = DEFAULT_SYNC_SECRET) -> bool:
    """Verify an HMAC-SHA256 signature on an incoming cloud snapshot."""
    expected = sign_snapshot_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


def sanitize_edge_properties(properties: dict[str, Any]) -> dict[str, Any]:
    """Sanitize sensitive credentials, secrets, or internal connection strings from edge metadata."""
    sanitized: dict[str, Any] = {}
    sensitive_keys = {"password", "secret", "token", "private_key", "api_key", "credentials"}

    for key, val in properties.items():
        key_lower = key.lower()
        if any(s in key_lower for s in sensitive_keys):
            sanitized[key] = "[REDACTED_FOR_EDGE_RUNTIME]"
        elif isinstance(val, dict):
            sanitized[key] = sanitize_edge_properties(val)
        else:
            sanitized[key] = val

    return sanitized


def validate_sync_token(token: str | None, secret: str = DEFAULT_SYNC_SECRET) -> bool:
    """Verify that the provided sync token matches the authorized edge secret."""
    if not token:
        return False
    return hmac.compare_digest(token, secret)
