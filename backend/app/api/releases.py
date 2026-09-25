"""FastAPI routes for Phase 9 Releases and Release Passports."""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.releases.passport_engine import ReleasePassportEngine
from app.models.agent import AgentRun
from app.models.change import ChangeRecord
from app.models.evidence import EvidenceRecord
from app.models.finding import Finding
from app.models.release import Release, ReleasePassport
from app.models.scenario import ScenarioRecord
from app.models.trust import PolicyDecision
from app.schemas.common import StandardResponse
from app.schemas.release import (
    ReleaseCreateRequest,
    ReleasePassportResponse,
    ReleaseResponse,
)

router = APIRouter(prefix="/releases", tags=["Releases"])


@router.post("", response_model=StandardResponse[ReleaseResponse], status_code=status.HTTP_201_CREATED)
async def create_release(
    payload: ReleaseCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ReleaseResponse]:
    """Register a new release bundle candidate."""
    release = Release(
        name=payload.name,
        version=payload.version,
        target_environment=payload.target_environment,
        commit_hash=payload.commit_hash,
        change_ids=payload.change_ids,
        status="pending",
    )
    db.add(release)
    await db.flush()
    await db.refresh(release)
    return StandardResponse(data=ReleaseResponse.model_validate(release))


@router.get("", response_model=StandardResponse[list[ReleaseResponse]])
async def list_releases(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[ReleaseResponse]]:
    """List release candidates."""
    query = select(Release).order_by(Release.created_at.desc())
    result = await db.execute(query)
    releases = result.scalars().all()
    return StandardResponse(
        data=[ReleaseResponse.model_validate(r) for r in releases],
        meta={"total": len(releases)},
    )


@router.get("/{release_id}", response_model=StandardResponse[ReleaseResponse])
async def get_release(
    release_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ReleaseResponse]:
    """Retrieve details of a release candidate."""
    query = select(Release).where(Release.id == release_id)
    result = await db.execute(query)
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    return StandardResponse(data=ReleaseResponse.model_validate(release))


@router.post("/{release_id}/passport", response_model=StandardResponse[ReleasePassportResponse])
async def issue_release_passport(
    release_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ReleasePassportResponse]:
    """Evaluate candidate against all verification domains and issue a verifiable Release Passport."""
    query = select(Release).where(Release.id == release_id).options(selectinload(Release.passport))
    result = await db.execute(query)
    release = result.scalar_one_or_none()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # Ingest verification domain data
    changes_res = await db.execute(select(ChangeRecord))
    changes = [c.to_dict() for c in changes_res.scalars().all()]

    findings_res = await db.execute(select(Finding))
    findings = [f.to_dict() for f in findings_res.scalars().all()]

    scenarios_res = await db.execute(select(ScenarioRecord))
    scenarios = [s.to_dict() for s in scenarios_res.scalars().all()]

    runs_res = await db.execute(select(AgentRun))
    agent_runs = [r.to_dict() for r in runs_res.scalars().all()]

    decisions_res = await db.execute(select(PolicyDecision))
    decisions = [d.to_dict() for d in decisions_res.scalars().all()]

    evidence_res = await db.execute(select(EvidenceRecord))
    evidence = [e.to_dict() for e in evidence_res.scalars().all()]

    passport_data = ReleasePassportEngine.generate_passport(
        release_version=release.version,
        changes=changes,
        findings=findings,
        scenarios=scenarios,
        agent_runs=agent_runs,
        policy_decisions=decisions,
        evidence_records=evidence,
    )

    if release.passport:
        passport = release.passport
        passport.overall_status = passport_data["overall_status"]
        passport.code_change_analysis = passport_data["code_change_analysis"]
        passport.context_findings = passport_data["context_findings"]
        passport.scenario_testing = passport_data["scenario_testing"]
        passport.agent_testing = passport_data["agent_testing"]
        passport.policy_validation = passport_data["policy_validation"]
        passport.evidence_completeness = passport_data["evidence_completeness"]
        passport.uncertainty_notes = passport_data["uncertainty_notes"]
        passport.passport_hash = passport_data["passport_hash"]
    else:
        passport = ReleasePassport(
            release_id=release.id,
            overall_status=passport_data["overall_status"],
            code_change_analysis=passport_data["code_change_analysis"],
            context_findings=passport_data["context_findings"],
            scenario_testing=passport_data["scenario_testing"],
            agent_testing=passport_data["agent_testing"],
            policy_validation=passport_data["policy_validation"],
            evidence_completeness=passport_data["evidence_completeness"],
            uncertainty_notes=passport_data["uncertainty_notes"],
            passport_hash=passport_data["passport_hash"],
        )
        db.add(passport)

    release.status = "certified" if passport_data["overall_status"] == "PASS" else "evaluated"
    await db.flush()
    await db.refresh(passport)

    return StandardResponse(data=ReleasePassportResponse.model_validate(passport))


@router.get("/{release_id}/passport", response_model=StandardResponse[ReleasePassportResponse])
async def get_release_passport(
    release_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ReleasePassportResponse]:
    """Retrieve existing Release Passport for a release."""
    query = select(ReleasePassport).where(ReleasePassport.release_id == release_id)
    result = await db.execute(query)
    passport = result.scalar_one_or_none()
    if not passport:
        raise HTTPException(status_code=404, detail="Release Passport not yet issued for this release candidate")
    return StandardResponse(data=ReleasePassportResponse.model_validate(passport))
