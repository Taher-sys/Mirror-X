"""Security sanitizer and path traversal protection utilities."""

import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

# Regular expressions and replacements for detecting sensitive tokens and secrets
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]{10,}", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(api[_-]?key\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-]{16,}['\"]?", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(secret\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-]{10,}['\"]?", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(password\s*[:=]\s*['\"]?)[^\s'\"]{6,}['\"]?", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(private_key\s*[:=]\s*['\"]?)[^\s'\"]+['\"]?", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE), "ghp_***REDACTED***"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "AKIA***REDACTED***"),
]

DISALLOWED_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.\.[/\\]"),  # Directory traversal (../ or ..\)
    re.compile(r"^[/\\]"),  # Absolute paths starting with / or \
    re.compile(r"^[a-zA-Z]:"),  # Windows drive letter (e.g., C:)
    re.compile(r"\x00"),  # Null byte injection
    re.compile(r":\$DATA"),  # Windows Alternate Data Streams
]


def sanitize_secrets(value: Any) -> Any:
    """Recursively scrub sensitive keys and token patterns from strings, dicts, or lists."""
    if isinstance(value, str):
        sanitized = value
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized
    elif isinstance(value, dict):
        scrubbed_dict: dict[str, Any] = {}
        for k, v in value.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("password", "secret", "token", "api_key", "private_key", "authorization")):
                scrubbed_dict[k] = "***REDACTED***"
            else:
                scrubbed_dict[k] = sanitize_secrets(v)
        return scrubbed_dict
    elif isinstance(value, (list, tuple)):
        return [sanitize_secrets(item) for item in value]
    return value


def is_safe_relative_path(path_str: str) -> bool:
    """Validate that a relative file path does not attempt path traversal or access outside root."""
    if not path_str or not isinstance(path_str, str):
        return False

    cleaned = path_str.strip()
    if not cleaned:
        return False

    # Check against disallowed injection patterns
    for pat in DISALLOWED_PATH_PATTERNS:
        if pat.search(cleaned):
            return False

    # Normalize path segments and check resolved depth
    norm_posix = PurePosixPath(cleaned)
    norm_windows = PureWindowsPath(cleaned)

    # Check for root or drive escape
    if norm_posix.is_absolute() or norm_windows.is_absolute():
        return False

    # Check for '..' in parts
    if ".." in norm_posix.parts or ".." in norm_windows.parts:
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters from filename while preserving legitimate extensions."""
    # Remove null bytes and non-printable characters
    cleaned = "".join(c for c in filename if c.isprintable() and c != "\x00")
    # Normalize forward slashes
    cleaned = cleaned.replace("\\", "/")
    # Remove leading slashes
    cleaned = cleaned.lstrip("/")
    # Disallow directory climbing
    parts = [p for p in cleaned.split("/") if p and p != ".." and p != "."]
    return "/".join(parts) if parts else "unnamed_file"
