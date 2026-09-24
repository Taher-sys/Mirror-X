"""System status and telemetry endpoints."""

import time
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.finding import Finding
from app.models.repository import Repository
from app.models.service import Service
from app.schemas.common import StandardResponse
from app.schemas.finding import FindingSeverityCounts
from app.schemas.system import SystemStatusResponse, SystemSummaryResponse

router = APIRouter(prefix="/system", tags=["System"])
settings = get_settings()

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

# Store server startup time
_STARTUP_TIME = time.time()


@router.get("/status", response_model=StandardResponse[SystemStatusResponse])
async def get_system_status(db: DatabaseSession) -> StandardResponse[SystemStatusResponse]:
    """Return real system operational and database status with latency."""
    t0 = time.perf_counter()
    db_connected = False
    dialect_name = "unknown"

    try:
        result = await db.execute(text("SELECT 1"))
        _ = result.scalar()
        db_connected = True
        dialect_name = db.bind.dialect.name if db.bind else "unknown"
    except (SQLAlchemyError, OSError):
        db_connected = False

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    uptime_seconds = round(time.time() - _STARTUP_TIME, 1)

    system_status = "healthy" if db_connected else "degraded"

    data = SystemStatusResponse(
        status=system_status,
        database_connected=db_connected,
        database_dialect=dialect_name,
        database_latency_ms=latency_ms,
        api_version=settings.app_version,
        uptime_seconds=uptime_seconds,
        timestamp=datetime.now(timezone.utc),
        active_connections=1,
    )
    return StandardResponse(data=data)


@router.get("/summary", response_model=StandardResponse[SystemSummaryResponse])
async def get_system_summary(db: DatabaseSession) -> StandardResponse[SystemSummaryResponse]:
    """Return real calculated metrics derived directly from stored entities."""

    # Count repositories
    repo_res = await db.execute(select(func.count(Repository.id)))
    repo_count = repo_res.scalar() or 0

    # Count services
    svc_res = await db.execute(select(func.count(Service.id)))
    svc_count = svc_res.scalar() or 0

    # Count healthy / degraded services
    healthy_res = await db.execute(
        select(func.count(Service.id)).where(Service.status == "healthy")
    )
    healthy_count = healthy_res.scalar() or 0

    degraded_res = await db.execute(
        select(func.count(Service.id)).where(Service.status != "healthy")
    )
    degraded_count = degraded_res.scalar() or 0

    # Count findings and breakdown by severity
    findings_total_res = await db.execute(select(func.count(Finding.id)))
    findings_total = findings_total_res.scalar() or 0

    severity_res = await db.execute(
        select(Finding.severity, func.count(Finding.id))
        .group_by(Finding.severity)
    )
    severity_map = {row[0].lower(): row[1] for row in severity_res.fetchall()}

    severity_counts = FindingSeverityCounts(
        critical=severity_map.get("critical", 0),
        high=severity_map.get("high", 0),
        medium=severity_map.get("medium", 0),
        low=severity_map.get("low", 0),
        info=severity_map.get("info", 0),
        total=findings_total,
    )

    # Derive overall system state based on real evidence
    if repo_count == 0 and svc_count == 0:
        system_status = "uninitialized"
    elif severity_counts.critical > 0 or degraded_count > 0:
        system_status = "degraded"
    else:
        system_status = "healthy"

    data = SystemSummaryResponse(
        repositories_count=repo_count,
        services_count=svc_count,
        findings_count=findings_total,
        findings_by_severity=severity_counts,
        services_healthy_count=healthy_count,
        services_degraded_count=degraded_count,
        system_status=system_status,
        timestamp=datetime.now(timezone.utc),
    )
    return StandardResponse(data=data)
