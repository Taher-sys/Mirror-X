"""FastAPI routes for Phase 8 Trust Layer."""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.trust.engine import DEFAULT_TRUST_POLICIES, TrustLayerEngine
from app.models.evidence import EvidenceRecord
from app.models.trust import (
    Permission,
    PolicyDecision,
    Principal,
    TrustAction,
    TrustPolicy,
    TrustResource,
)
from app.schemas.common import StandardResponse
from app.schemas.trust import (
    EvaluatePolicyRequest,
    EvaluatePolicyResponse,
    PermissionResponse,
    PolicyDecisionResponse,
    PolicyDecisionReviewRequest,
    TrustPolicyCreateRequest,
    TrustPolicyResponse,
    TrustResourceResponse,
)

router = APIRouter(prefix="/trust", tags=["Trust Layer"])


@router.get("/policies", response_model=StandardResponse[list[dict[str, Any]]])
async def list_policies(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[dict[str, Any]]]:
    """List governance policies."""
    query = select(TrustPolicy).order_by(TrustPolicy.name)
    result = await db.execute(query)
    policies = result.scalars().all()
    if not policies:
        # Return default loaded policies
        return StandardResponse(data=DEFAULT_TRUST_POLICIES, meta={"total": len(DEFAULT_TRUST_POLICIES)})
    return StandardResponse(
        data=[TrustPolicyResponse.model_validate(p).model_dump() for p in policies],
        meta={"total": len(policies)},
    )


@router.post("/policies", response_model=StandardResponse[TrustPolicyResponse], status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: TrustPolicyCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[TrustPolicyResponse]:
    """Create a new Trust Layer policy."""
    policy = TrustPolicy(
        name=payload.name,
        description=payload.description,
        enforcement_level=payload.enforcement_level,
        target_type=payload.target_type,
        rules_payload=payload.rules_payload,
        is_active=payload.is_active,
    )
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return StandardResponse(data=TrustPolicyResponse.model_validate(policy))


@router.get("/permissions", response_model=StandardResponse[list[dict[str, Any]]])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[dict[str, Any]]]:
    """List permissions and role-resource bindings."""
    query = select(Permission).order_by(Permission.name)
    result = await db.execute(query)
    perms = result.scalars().all()

    default_permissions = [
        {"name": "perm_agent_sandbox_read", "principal_role": "agent", "resource_type": "database", "action_name": "read", "effect": "ALLOW", "conditions": {"sandbox_only": True}},
        {"name": "perm_agent_sandbox_invoke", "principal_role": "agent", "resource_type": "api_endpoint", "action_name": "invoke", "effect": "ALLOW", "conditions": {"sandbox_only": True}},
        {"name": "perm_agent_schema_alter", "principal_role": "agent", "resource_type": "database", "action_name": "schema_alter", "effect": "DENY", "conditions": {}},
        {"name": "perm_human_admin_all", "principal_role": "admin", "resource_type": "all", "action_name": "all", "effect": "ALLOW", "conditions": {}},
    ]

    data = [PermissionResponse.model_validate(p).model_dump() for p in perms] if perms else default_permissions
    return StandardResponse(data=data, meta={"total": len(data)})


@router.get("/resources", response_model=StandardResponse[list[dict[str, Any]]])
async def list_trust_resources(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[dict[str, Any]]]:
    """List resources under Trust Layer governance (all marked sandbox=True)."""
    default_resources = [
        {"name": "sandbox-orders-db", "resource_type": "database", "classification": "internal", "is_sandbox": True},
        {"name": "sandbox-checkout-api", "resource_type": "api_endpoint", "classification": "internal", "is_sandbox": True},
        {"name": "sandbox-customers-table", "resource_type": "table", "classification": "confidential", "is_sandbox": True},
        {"name": "sandbox-auth-service", "resource_type": "service", "classification": "restricted", "is_sandbox": True},
    ]
    return StandardResponse(data=default_resources, meta={"total": len(default_resources)})


@router.post("/evaluate", response_model=StandardResponse[EvaluatePolicyResponse])
async def evaluate_policy_request(
    payload: EvaluatePolicyRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[EvaluatePolicyResponse]:
    """Evaluate an action against policies: returns ALLOW, DENY, or HUMAN_REVIEW_REQUIRED."""
    engine = TrustLayerEngine()
    eval_result = engine.evaluate(
        principal_name=payload.principal_name,
        resource_name=payload.resource_name,
        action_name=payload.action_name,
        agent_name=payload.agent_name,
        tool_name=payload.tool_name,
        resource_classification=payload.resource_classification,
        is_sandbox=payload.is_sandbox,
        context=payload.context,
    )

    evidence_id = None
    if eval_result.get("evidence"):
        ev_data = eval_result["evidence"]
        evidence_record = EvidenceRecord(
            evidence_type=ev_data["evidence_type"],
            source_reference=ev_data["source_reference"],
            summary=ev_data["summary"],
            raw_payload=ev_data["raw_payload"],
            hash_signature=ev_data["hash_signature"],
            confidence=ev_data["confidence"],
        )
        db.add(evidence_record)
        await db.flush()
        evidence_id = str(evidence_record.id)

    # Persist decision
    decision = PolicyDecision(
        principal_name=payload.principal_name,
        agent_name=payload.agent_name,
        tool_name=payload.tool_name,
        resource_name=payload.resource_name,
        action_name=payload.action_name,
        result=eval_result["result"],
        reason=eval_result["reason"],
        matched_policies=eval_result["matched_policies"],
        context_snapshot=payload.context,
        evidence_id=evidence_id,
    )
    db.add(decision)
    await db.flush()

    return StandardResponse(
        data=EvaluatePolicyResponse(
            result=eval_result["result"],
            reason=eval_result["reason"],
            matched_policies=eval_result["matched_policies"],
            evidence=eval_result["evidence"],
            is_sandbox=eval_result["is_sandbox"],
        )
    )


@router.get("/decisions", response_model=StandardResponse[list[PolicyDecisionResponse]])
async def list_decisions(
    result_filter: str | None = Query(None, description="ALLOW, DENY, HUMAN_REVIEW_REQUIRED"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[PolicyDecisionResponse]]:
    """List policy decisions and audit trail."""
    query = select(PolicyDecision).order_by(PolicyDecision.created_at.desc()).limit(limit)
    if result_filter:
        query = query.where(PolicyDecision.result == result_filter.upper())

    res = await db.execute(query)
    decisions = res.scalars().all()
    return StandardResponse(
        data=[PolicyDecisionResponse.model_validate(d) for d in decisions],
        meta={"total": len(decisions)},
    )


@router.post("/decisions/{decision_id}/review", response_model=StandardResponse[PolicyDecisionResponse])
async def review_policy_decision(
    decision_id: uuid.UUID,
    payload: PolicyDecisionReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PolicyDecisionResponse]:
    """Human-in-the-loop sign-off for review-required decisions."""
    query = select(PolicyDecision).where(PolicyDecision.id == decision_id)
    res = await db.execute(query)
    decision = res.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.review_status = payload.review_status
    decision.reviewed_by = payload.reviewed_by
    await db.flush()

    return StandardResponse(data=PolicyDecisionResponse.model_validate(decision))
