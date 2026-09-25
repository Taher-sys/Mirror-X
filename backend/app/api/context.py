"""Context Engine API endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context.engine import ContextEngine
from app.core.database import get_db
from app.models.finding import Finding
from app.models.graph import GraphNode
from app.schemas.finding import FindingResponse

router = APIRouter(prefix="/context", tags=["Context Engine"])


class AnalyzeRequest(BaseModel):
    """Request payload to trigger discrepancy analysis."""

    repository_id: uuid.UUID | None = None
    file_tree: dict[str, str] | None = None


class ContextStatsResponse(BaseModel):
    """Statistics for discrepancy findings."""

    total_findings: int
    findings_by_type: dict[str, int]
    findings_by_severity: dict[str, int]
    findings_by_status: dict[str, int]
    resolution_rate: float


class UpdateFindingStatusRequest(BaseModel):
    """Request payload to update finding status."""

    status: str  # open, resolved, dismissed


@router.post("/analyze", response_model=list[FindingResponse], status_code=status.HTTP_200_OK)
async def analyze_context(
    request: AnalyzeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Execute discrepancy detectors against the Reality Graph and codebase."""
    engine = ContextEngine()
    findings = await engine.analyze_repository(
        db=db,
        repository_id=request.repository_id,
        file_tree=request.file_tree,
    )
    return [FindingResponse.model_validate(f) for f in findings]


@router.get("/findings", response_model=list[FindingResponse])
async def list_context_findings(
    db: Annotated[AsyncSession, Depends(get_db)],
    finding_type: Annotated[str | None, Query(description="Filter by finding type")] = None,
    severity: Annotated[str | None, Query(description="Filter by severity")] = None,
    status_filter: Annotated[str | None, Query(alias="status", description="Filter by status")] = None,
    repository_id: Annotated[uuid.UUID | None, Query(description="Filter by repository ID")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> Any:
    """Retrieve filtered analytical findings and discrepancies."""
    stmt = select(Finding).order_by(Finding.created_at.desc())

    if finding_type:
        stmt = stmt.where(Finding.finding_type == finding_type)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status_filter:
        stmt = stmt.where(Finding.status == status_filter)
    if repository_id:
        stmt = stmt.where(Finding.repository_id == repository_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/findings/{finding_id}")
async def get_finding_detail(
    finding_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Get single finding detail including linked Reality Graph nodes."""
    res = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID {finding_id} not found",
        )

    # Resolve related nodes from evidence payload if present
    related_nodes: list[dict[str, Any]] = []
    if finding.evidence_payload and "related_node_ids" in finding.evidence_payload:
        node_ids = finding.evidence_payload["related_node_ids"]
        if node_ids:
            try:
                uuids = [uuid.UUID(nid) for nid in node_ids if isinstance(nid, str)]
                if uuids:
                    n_res = await db.execute(select(GraphNode).where(GraphNode.id.in_(uuids)))
                    related_nodes = [
                        {
                            "id": str(n.id),
                            "name": n.name,
                            "node_type": n.node_type,
                            "path": n.path,
                            "properties": n.properties,
                        }
                        for n in n_res.scalars().all()
                    ]
            except (ValueError, TypeError):
                related_nodes = []

    return {
        "finding": FindingResponse.model_validate(finding),
        "related_nodes": related_nodes,
    }


@router.patch("/findings/{finding_id}", response_model=FindingResponse)
async def update_finding_status(
    finding_id: uuid.UUID,
    request: UpdateFindingStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Update status of a discrepancy finding."""
    res = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID {finding_id} not found",
        )

    valid_statuses = {"open", "resolved", "dismissed"}
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{request.status}'. Must be one of {valid_statuses}",
        )

    finding.status = request.status
    await db.commit()
    await db.refresh(finding)
    return finding


@router.get("/statistics", response_model=ContextStatsResponse)
async def get_context_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    repository_id: Annotated[uuid.UUID | None, Query()] = None,
) -> Any:
    """Compute real statistics on discrepancy findings without fabricated numbers."""
    base_stmt = select(Finding)
    if repository_id:
        base_stmt = base_stmt.where(Finding.repository_id == repository_id)

    res = await db.execute(base_stmt)
    findings = res.scalars().all()

    total = len(findings)
    by_type: dict[str, int] = {}
    by_sev: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_status: dict[str, int] = {"open": 0, "resolved": 0, "dismissed": 0}

    for f in findings:
        by_type[f.finding_type] = by_type.get(f.finding_type, 0) + 1
        sev = f.severity.lower()
        by_sev[sev] = by_sev.get(sev, 0) + 1
        stat = f.status.lower()
        by_status[stat] = by_status.get(stat, 0) + 1

    resolved = by_status.get("resolved", 0)
    resolution_rate = round(resolved / total, 4) if total > 0 else 0.0

    return ContextStatsResponse(
        total_findings=total,
        findings_by_type=by_type,
        findings_by_severity=by_sev,
        findings_by_status=by_status,
        resolution_rate=resolution_rate,
    )
