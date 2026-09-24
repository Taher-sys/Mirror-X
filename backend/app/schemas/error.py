"""Error response schemas."""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: list[Any] | None = None


class ErrorResponse(BaseModel):
    """Standardized error response envelope."""

    status: str = "error"
    error: ErrorDetail
