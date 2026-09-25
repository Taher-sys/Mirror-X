"""Pydantic schemas for Synthetic Scenario Engine."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreateRequest(BaseModel):
    """Request payload to generate a synthetic scenario."""

    target_name: str = Field(..., description="Target entity or API name")
    source_type: str = Field(
        "api",
        description="Source type: api, schema, domain_model, policy, tool_definition, validation_rule, existing_test",
    )
    scenario_class: str = Field(
        "normal",
        description="Scenario class: normal, boundary, incomplete, malformed, contradictory, unauthorized, adversarial, outage, tool_failure, ambiguous",
    )
    seed: int = Field(42, description="Random seed for reproducible generation")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Optional overrides or parameters")


class ScenarioResponse(BaseModel):
    """Serialized synthetic test scenario."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    scenario_class: str
    source_type: str
    seed: int
    initial_state: dict[str, Any]
    generated_inputs: dict[str, Any]
    expected_constraints: dict[str, Any]
    participating_resources: list[Any]
    applicable_policies: list[Any]
    metadata_payload: dict[str, Any]
    status: str
    execution_result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioExecutionResult(BaseModel):
    """Result of executing a scenario in the sandbox harness."""

    execution_id: str
    scenario_id: str
    status: str
    passed: bool
    actual_status: int
    actual_decision: str
    matched_constraints: list[str]
    evidence_generated: bool
    execution_duration_ms: float
    timestamp: str
