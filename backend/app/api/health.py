"""Health check API endpoint."""

from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Status indicating service health.
    """
    return HealthResponse(status="healthy")
