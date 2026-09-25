"""Standardized error handling per API contract with production security hardening."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions with sanitized standardized response."""
    from app.core.security.sanitizer import sanitize_secrets

    sanitized_details = sanitize_secrets(exc.details) if exc.details else None
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=sanitized_details,
            )
        ).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation exceptions securely without leaking internal paths."""
    clean_errors = []
    for err in exc.errors():
        clean_errors.append(
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "issue": err.get("msg", "Invalid input"),
                "type": err.get("type", "value_error"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request payload validation failed.",
                details=clean_errors,
            )
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with safe generic error response in production."""
    # In production, never return internal stack trace or raw exception details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected server error occurred. Please contact system administrator.",
                details=None,
            )
        ).model_dump(),
    )
