"""Pydantic schemas for Trust Layer."""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class TrustPolicyResponse(BaseModel):
    """Governance policy definition."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    enforcement_level: str
    target_type: str
    rules_payload: dict[str, Any]
    is_active: bool
    created_at: datetime


class TrustPolicyCreateRequest(BaseModel):
    """Payload to register a governance policy."""

    name: str
    description: str
    enforcement_level: str = "strict"
    target_type: str = "all"
    rules_payload: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PermissionResponse(BaseModel):
    """Permission binding."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    principal_role: str
    resource_type: str
    action_name: str
    effect: str
    conditions: dict[str, Any]
    created_at: datetime


class TrustResourceResponse(BaseModel):
    """Protected resource representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    resource_type: str
    classification: str
    is_sandbox: bool
    properties: dict[str, Any]
    created_at: datetime


class EvaluatePolicyRequest(BaseModel):
    """Evaluate an action request against policies."""

    principal_name: str = Field(..., description="Identity invoking the action")
    resource_name: str = Field(..., description="Target resource")
    action_name: str = Field(..., description="Action operation name")
    agent_name: str | None = Field(None, description="Optional agent name")
    tool_name: str | None = Field(None, description="Optional tool name")
    resource_classification: str = Field("internal", description="public, internal, confidential, restricted")
    is_sandbox: bool = Field(True, description="Must be True for safe sandbox execution")
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluatePolicyResponse(BaseModel):
    """Evaluation result from the Trust Layer."""

    result: str  # ALLOW, DENY, HUMAN_REVIEW_REQUIRED
    reason: str
    matched_policies: list[str]
    evidence: dict[str, Any] | None = None
    is_sandbox: bool


class PolicyDecisionResponse(BaseModel):
    """Audit record of a policy decision."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    principal_name: str
    agent_name: str | None = None
    tool_name: str | None = None
    resource_name: str
    action_name: str
    result: str
    reason: str
    matched_policies: list[Any]
    context_snapshot: dict[str, Any]
    evidence_id: str | None = None
    reviewed_by: str | None = None
    review_status: str | None = None
    created_at: datetime


class PolicyDecisionReviewRequest(BaseModel):
    """Human-in-the-loop review approval or rejection."""

    review_status: str = Field(..., description="approved or rejected")
    reviewed_by: str = Field(..., description="Identity of reviewer")
