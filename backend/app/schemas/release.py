"""Pydantic schemas for Evidence Ledger and Release Passport."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreateRequest(BaseModel):
    """Payload to record an immutable evidence record."""

    evidence_type: str = Field(
        ...,
        description="source_file, graph_relationship, api_contract, test_execution, scenario_run, agent_execution, policy_decision, runtime_trace",
    )
    source_reference: str = Field(..., description="Path, URI, or ID of source")
    summary: str = Field(..., description="Summary description of the ground truth artifact")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Verifiable content artifact")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    linked_finding_id: str | None = None
    linked_change_id: str | None = None


class EvidenceResponse(BaseModel):
    """Verifiable evidence record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evidence_type: str
    source_reference: str
    summary: str
    raw_payload: dict[str, Any]
    hash_signature: str
    confidence: float
    linked_finding_id: str | None = None
    linked_change_id: str | None = None
    created_at: datetime


class ReleaseCreateRequest(BaseModel):
    """Payload to register a release bundle candidate."""

    name: str
    version: str
    target_environment: str = "staging"
    commit_hash: str
    change_ids: list[str] = Field(default_factory=list)


class ReleaseResponse(BaseModel):
    """Release entity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    target_environment: str
    commit_hash: str
    change_ids: list[Any]
    status: str
    created_at: datetime


class ReleasePassportResponse(BaseModel):
    """Release Passport certification artifact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    release_id: uuid.UUID
    overall_status: str  # PASS, FAIL, WARNING, HUMAN_REVIEW_REQUIRED, NOT_EVALUATED
    code_change_analysis: dict[str, Any]
    context_findings: dict[str, Any]
    scenario_testing: dict[str, Any]
    agent_testing: dict[str, Any]
    policy_validation: dict[str, Any]
    evidence_completeness: dict[str, Any]
    uncertainty_notes: str
    passport_hash: str
    created_at: datetime
