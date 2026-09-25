"""FastAPI routes for Phase 9 Evidence Ledger."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.evidence import EvidenceRecord
from app.schemas.common import StandardResponse
from app.schemas.release import EvidenceCreateRequest, EvidenceResponse

router = APIRouter(prefix="/evidence", tags=["Evidence Ledger"])


@router.post("", response_model=StandardResponse[EvidenceResponse], status_code=status.HTTP_201_CREATED)
async def create_evidence(
    payload: EvidenceCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[EvidenceResponse]:
    """Record a new immutable evidence record in the ledger."""
    hash_sig = EvidenceRecord.calculate_hash(payload.raw_payload, payload.source_reference)
    record = EvidenceRecord(
        evidence_type=payload.evidence_type,
        source_reference=payload.source_reference,
        summary=payload.summary,
        raw_payload=payload.raw_payload,
        hash_signature=hash_sig,
        confidence=payload.confidence,
        linked_finding_id=payload.linked_finding_id,
        linked_change_id=payload.linked_change_id,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return StandardResponse(data=EvidenceResponse.model_validate(record))


@router.get("", response_model=StandardResponse[list[EvidenceResponse]])
async def list_evidence(
    evidence_type: str | None = Query(
        None,
        description="source_file, graph_relationship, api_contract, test_execution, scenario_run, agent_execution, policy_decision, runtime_trace",
    ),
    search: str | None = Query(None, description="Search term in summary or source reference"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[EvidenceResponse]]:
    """Query immutable evidence records."""
    query = select(EvidenceRecord).order_by(EvidenceRecord.created_at.desc()).limit(limit)
    if evidence_type:
        query = query.where(EvidenceRecord.evidence_type == evidence_type)
    if search:
        query = query.where(
            or_(
                EvidenceRecord.summary.ilike(f"%{search}%"),
                EvidenceRecord.source_reference.ilike(f"%{search}%"),
            )
        )

    result = await db.execute(query)
    records = result.scalars().all()
    return StandardResponse(
        data=[EvidenceResponse.model_validate(r) for r in records],
        meta={"total": len(records)},
    )


@router.get("/{evidence_id}", response_model=StandardResponse[EvidenceResponse])
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[EvidenceResponse]:
    """Retrieve an evidence record and verify its cryptographic hash."""
    query = select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    # Verify cryptographic integrity
    expected_hash = EvidenceRecord.calculate_hash(record.raw_payload, record.source_reference)
    if expected_hash != record.hash_signature:
        raise HTTPException(status_code=409, detail="Evidence hash integrity mismatch! Tamper detected.")

    return StandardResponse(data=EvidenceResponse.model_validate(record))
