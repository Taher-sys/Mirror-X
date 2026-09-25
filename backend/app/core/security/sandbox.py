"""Repository ingestion sandboxing and execution isolation boundaries."""

from typing import Any

from app.core.errors import AppException
from app.core.security.sanitizer import is_safe_relative_path

# Security constraints for ingestion sandboxing
MAX_FILES_PER_INGESTION = 500
MAX_SINGLE_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_TOTAL_PAYLOAD_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

# Disallowed binary or executable extensions that have no business in architecture ingestion
DISALLOWED_EXTENSIONS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pyc",
    ".pyd",
    ".class",
    ".jar",
    ".war",
    ".cmd",
    ".vbs",
    ".ps1",
}


class IngestionSandboxViolation(AppException):
    """Raised when repository payload violates ingestion sandbox security bounds."""

    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__(
            code="INGESTION_SANDBOX_VIOLATION",
            message=message,
            status_code=400,
            details=details,
        )


def validate_ingestion_payload(files: dict[str, str]) -> None:
    """Strictly validate repository ingestion files dictionary against sandboxing rules.

    Guarantees:
    1. Total file count is bounded to prevent resource exhaustion / DoS.
    2. Single file size and aggregate size are bounded.
    3. Every file path is validated against directory traversal and null byte injections.
    4. Executable/binary payloads are rejected.
    5. Ingestion takes place exclusively in-memory with zero subprocess or shell execution.
    """
    if not isinstance(files, dict):
        raise IngestionSandboxViolation("Ingestion files payload must be a key-value dictionary.")

    if not files:
        raise IngestionSandboxViolation("Ingestion files payload cannot be empty.")

    if len(files) > MAX_FILES_PER_INGESTION:
        raise IngestionSandboxViolation(
            f"File count exceeds maximum allowed limit of {MAX_FILES_PER_INGESTION} files (received {len(files)})."
        )

    total_bytes = 0
    for file_path, content in files.items():
        if not isinstance(file_path, str) or not is_safe_relative_path(file_path):
            raise IngestionSandboxViolation(f"Potentially malicious or invalid file path detected: '{file_path}'")

        # Check file extension against disallowed binaries
        lower_path = file_path.lower()
        if any(lower_path.endswith(ext) for ext in DISALLOWED_EXTENSIONS):
            raise IngestionSandboxViolation(
                f"Binary or executable file types are disallowed in Reality Graph ingestion: '{file_path}'"
            )

        if not isinstance(content, str):
            raise IngestionSandboxViolation(f"File content for '{file_path}' must be a valid UTF-8 string.")

        content_bytes = len(content.encode("utf-8", errors="replace"))
        if content_bytes > MAX_SINGLE_FILE_SIZE_BYTES:
            raise IngestionSandboxViolation(
                f"File '{file_path}' exceeds maximum size of {MAX_SINGLE_FILE_SIZE_BYTES // (1024 * 1024)}MB "
                f"({content_bytes} bytes)."
            )

        total_bytes += content_bytes
        if total_bytes > MAX_TOTAL_PAYLOAD_SIZE_BYTES:
            raise IngestionSandboxViolation(
                f"Total ingestion payload size exceeds limit of {MAX_TOTAL_PAYLOAD_SIZE_BYTES // (1024 * 1024)}MB."
            )
