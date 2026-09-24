"""Change Twin API endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.changes.impact_engine import ChangeImpactEngine
from app.core.database import get_db
from app.models.change import ChangeRecord
from app.models.graph import GraphEdge, GraphNode

router = APIRouter(prefix="/changes", tags=["Change Twin"])


class AnalyzeImpactRequest(BaseModel):
    """Request payload to analyze impact of a Git diff."""

    title: str = Field(default="Proposed Code Change", max_length=255)
    git_diff: str = Field(..., min_length=1)
    repository_id: uuid.UUID | None = None
    branch: str | None = None
    author: str | None = None


class ChangeRecordResponse(BaseModel):
    """Response model for a change record."""

    id: uuid.UUID
    title: str
    branch: str | None = None
    author: str | None = None
    git_diff: str
    direct_impact_count: int
    indirect_impact_count: int
    risk_score: float
    risk_level: str
    impact_summary: dict[str, Any]
    repository_id: uuid.UUID | None = None
    created_at: Any
    updated_at: Any


@router.post("/impact", status_code=status.HTTP_200_OK)
async def analyze_change_impact(
    request: AnalyzeImpactRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Analyze a Git diff against the Reality Graph to determine direct and indirect blast radius."""
    # 1. Fetch graph nodes and edges
    stmt_nodes = select(GraphNode)
    stmt_edges = select(GraphEdge)
    if request.repository_id:
        stmt_nodes = stmt_nodes.where(
            (GraphNode.repository_id == request.repository_id) | (GraphNode.repository_id.is_(None))
        )

    res_nodes = await db.execute(stmt_nodes)
    nodes_db = res_nodes.scalars().all()

    res_edges = await db.execute(stmt_edges)
    edges_db = res_edges.scalars().all()

    nodes_payload = [
        {
            "id": str(n.id),
            "name": n.name,
            "node_type": n.node_type,
            "path": n.path,
            "properties": n.properties or {},
            "repository_id": str(n.repository_id) if n.repository_id else None,
        }
        for n in nodes_db
    ]

    edges_payload = [
        {
            "id": str(e.id),
            "source_node_id": str(e.source_node_id),
            "target_node_id": str(e.target_node_id),
            "relationship_type": e.relationship_type,
            "properties": e.properties or {},
        }
        for e in edges_db
    ]

    # 2. Run Impact Engine
    engine = ChangeImpactEngine()
    analysis = engine.analyze(
        diff_text=request.git_diff,
        nodes=nodes_payload,
        edges=edges_payload,
    )
    result_dict = analysis.to_dict()

    # 3. Persist ChangeRecord
    record = ChangeRecord(
        title=request.title,
        branch=request.branch,
        author=request.author,
        git_diff=request.git_diff,
        direct_impact_count=result_dict["direct_impact_count"],
        indirect_impact_count=result_dict["indirect_impact_count"],
        risk_score=result_dict["risk_score"],
        risk_level=result_dict["risk_level"],
        impact_summary=result_dict,
        repository_id=request.repository_id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "record_id": str(record.id),
        "title": record.title,
        "branch": record.branch,
        "author": record.author,
        "created_at": record.created_at,
        **result_dict,
    }


@router.get("", response_model=list[ChangeRecordResponse])
async def list_change_records(
    db: Annotated[AsyncSession, Depends(get_db)],
    repository_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Any:
    """Retrieve history of analyzed changes and simulated diffs."""
    stmt = select(ChangeRecord).order_by(ChangeRecord.created_at.desc())
    if repository_id:
        stmt = stmt.where(ChangeRecord.repository_id == repository_id)
    stmt = stmt.limit(limit)

    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{change_id}", response_model=ChangeRecordResponse)
async def get_change_record(
    change_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Retrieve specific change record impact details."""
    res = await db.execute(select(ChangeRecord).where(ChangeRecord.id == change_id))
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Change record {change_id} not found",
        )
    return record
