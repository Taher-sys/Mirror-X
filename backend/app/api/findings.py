from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.errors import AppException
from app.models.activity import Activity
from app.models.finding import Finding
from app.models.repository import Repository
from app.models.service import Service
from app.schemas.common import PaginationMeta, StandardResponse
from app.schemas.finding import (
    FindingCreate,
    FindingResponse,
    FindingSeverityCounts,
)

router = APIRouter(prefix="/findings", tags=["Findings"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=StandardResponse[list[FindingResponse]])
async def list_findings(
    db: DatabaseSession,
    severity: Annotated[str | None, Query(description="Filter by severity (critical, high, medium, low, info)")] = None,
    finding_type: Annotated[str | None, Query(description="Filter by finding type")] = None,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status (open, resolved, dismissed)")
    ] = None,
    search: Annotated[str | None, Query(description="Search term for finding title or description")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> StandardResponse[list[FindingResponse]]:
    """List findings with filters and pagination."""
    query = select(Finding).options(
        selectinload(Finding.repository),
        selectinload(Finding.service),
    )

    if severity:
        query = query.where(Finding.severity == severity.lower())
    if finding_type:
        query = query.where(Finding.finding_type == finding_type)
    if status_filter:
        query = query.where(Finding.status == status_filter)
    if search:
        search_filter = f"%{search}%"
        query = query.where((Finding.title.ilike(search_filter)) | (Finding.description.ilike(search_filter)))

    # Count query
    count_query = select(func.count(Finding.id))
    if severity:
        count_query = count_query.where(Finding.severity == severity.lower())
    if finding_type:
        count_query = count_query.where(Finding.finding_type == finding_type)
    if status_filter:
        count_query = count_query.where(Finding.status == status_filter)
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.where(
            (Finding.title.ilike(search_filter)) | (Finding.description.ilike(search_filter))
        )
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Finding.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    findings = result.scalars().all()

    items = [
        FindingResponse(
            id=f.id,
            title=f.title,
            finding_type=f.finding_type,
            severity=f.severity,
            confidence=f.confidence,
            description=f.description,
            evidence_payload=f.evidence_payload,
            status=f.status,
            repository_id=f.repository_id,
            service_id=f.service_id,
            repository_name=f.repository.name if f.repository else None,
            service_name=f.service.name if f.service else None,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in findings
    ]

    meta = PaginationMeta(
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    ).model_dump()

    return StandardResponse(data=items, meta=meta)


@router.get("/summary", response_model=StandardResponse[FindingSeverityCounts])
async def get_findings_summary(
    db: DatabaseSession,
) -> StandardResponse[FindingSeverityCounts]:
    """Get aggregated severity count breakdown."""
    total_res = await db.execute(select(func.count(Finding.id)))
    total = total_res.scalar() or 0

    severity_res = await db.execute(select(Finding.severity, func.count(Finding.id)).group_by(Finding.severity))
    severity_map = {row[0].lower(): row[1] for row in severity_res.fetchall()}

    counts = FindingSeverityCounts(
        critical=severity_map.get("critical", 0),
        high=severity_map.get("high", 0),
        medium=severity_map.get("medium", 0),
        low=severity_map.get("low", 0),
        info=severity_map.get("info", 0),
        total=total,
    )
    return StandardResponse(data=counts)


@router.post("", response_model=StandardResponse[FindingResponse], status_code=status.HTTP_201_CREATED)
async def create_finding(
    payload: FindingCreate,
    db: DatabaseSession,
) -> StandardResponse[FindingResponse]:
    """Create a new analytical finding."""
    if payload.repository_id:
        repo = await db.get(Repository, payload.repository_id)
        if not repo:
            raise AppException(
                code="REPOSITORY_NOT_FOUND",
                message=f"Repository with ID '{payload.repository_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    if payload.service_id:
        svc = await db.get(Service, payload.service_id)
        if not svc:
            raise AppException(
                code="SERVICE_NOT_FOUND",
                message=f"Service with ID '{payload.service_id}' not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    finding = Finding(
        title=payload.title,
        finding_type=payload.finding_type,
        severity=payload.severity.lower(),
        confidence=payload.confidence,
        description=payload.description,
        evidence_payload=payload.evidence_payload,
        status=payload.status,
        repository_id=payload.repository_id,
        service_id=payload.service_id,
    )
    db.add(finding)
    await db.flush()

    activity = Activity(
        actor="system",
        action="finding_detected",
        entity_type="finding",
        entity_name=finding.title,
        details=f"[{finding.severity.upper()}] {finding.title} detected ({finding.finding_type})",
    )
    db.add(activity)
    await db.commit()
    await db.refresh(finding)

    return StandardResponse(
        data=FindingResponse(
            id=finding.id,
            title=finding.title,
            finding_type=finding.finding_type,
            severity=finding.severity,
            confidence=finding.confidence,
            description=finding.description,
            evidence_payload=finding.evidence_payload,
            status=finding.status,
            repository_id=finding.repository_id,
            service_id=finding.service_id,
            created_at=finding.created_at,
            updated_at=finding.updated_at,
        )
    )
