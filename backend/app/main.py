"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.edge.database import get_edge_db_manager
from app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.observability import ObservabilityMiddleware
from app.core.security.rate_limit import RateLimitMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await init_db()
    await get_edge_db_manager().init_db()
    yield
    # Shutdown
    await get_edge_db_manager().close()
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Reality Twin for AI-Native Software Systems",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # 1. CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. OpenTelemetry Tracing middleware
    app.add_middleware(ObservabilityMiddleware)

    # 3. Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        default_limit=settings.rate_limit_per_minute,
        sensitive_limit=settings.rate_limit_sensitive_per_minute,
    )

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include routers
    app.include_router(api_router)
    from app.api.edge import router as edge_router

    app.include_router(edge_router, prefix="/api")

    return app


app = create_app()
