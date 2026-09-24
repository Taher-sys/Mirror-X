"""API routes aggregation."""

from fastapi import APIRouter

from app.api.activities import router as activities_router
from app.api.changes import router as changes_router
from app.api.context import router as context_router
from app.api.findings import router as findings_router
from app.api.graph import router as graph_router
from app.api.health import router as health_router
from app.api.repositories import router as repositories_router
from app.api.services import router as services_router
from app.api.system import router as system_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(system_router)
api_router.include_router(repositories_router)
api_router.include_router(services_router)
api_router.include_router(findings_router)
api_router.include_router(activities_router)
api_router.include_router(graph_router)
api_router.include_router(context_router)
api_router.include_router(changes_router)

__all__ = ["api_router"]


