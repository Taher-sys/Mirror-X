"""Common schema definitions and API envelopes."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int = 1
    limit: int = 50
    pages: int = 1


class StandardResponse(BaseModel, Generic[T]):
    """Standardized API response envelope per API contract."""

    status: str = "success"
    data: T
    meta: dict[str, Any] | None = None
