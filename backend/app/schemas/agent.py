"""Pydantic schemas for Agent Behavior Lab."""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AgentCreateRequest(BaseModel):
    """Payload to register an agent version."""

    name: str = Field(..., description="Agent name")
    version: str = Field("v1.0.0", description="Semver agent version")
    model_reference: str = Field("gpt-4o", description="Underlying model reference")
    purpose: str = Field(..., description="Agent purpose / mission description")
    config_payload: dict[str, Any] = Field(default_factory=dict, description="Configuration")


class AgentToolResponse(BaseModel):
    """Available sandbox tool for agent execution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    description: str
    parameters_schema: dict[str, Any]
    risk_level: str
    is_mock_safe: bool


class AgentStepResponse(BaseModel):
    """Discrete step within an AgentRun."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    thought: str
    tool_call: str | None = None
    arguments: dict[str, Any]
    tool_output: dict[str, Any] | None = None
    policy_check: dict[str, Any]
    duration_ms: float
    status: str
    error: str | None = None


class AgentResponse(BaseModel):
    """Agent entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    model_reference: str
    purpose: str
    status: str
    config_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AgentRunRequest(BaseModel):
    """Trigger an agent execution run in the sandbox lab."""

    goal: str = Field(..., description="Target objective or task")
    context_reference: dict[str, Any] = Field(default_factory=dict, description="Contextual entity references")
    scenario_inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs from synthetic scenario")


class AgentRunResponse(BaseModel):
    """Detailed telemetry record of an AgentRun."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    agent_version: str
    goal: str
    context_reference: dict[str, Any]
    model_reference: str
    trace_id: str
    plan: list[Any]
    status: str
    result: dict[str, Any] | None = None
    errors: list[Any]
    timings: dict[str, Any]

    # Measurable behavior metrics
    successful_completion: bool
    correct_tool_selection_count: int
    incorrect_tool_use_count: int
    unnecessary_actions_count: int
    policy_violations_count: int
    error_count: int
    latency_ms: float
    retry_count: int

    steps: list[AgentStepResponse] = []
    created_at: datetime


class AgentCompareRequest(BaseModel):
    """Request to compare measurable behaviors between two agent runs or versions."""

    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID


class AgentCompareResponse(BaseModel):
    """Measurable behavioral comparison matrix."""

    baseline_version: str
    candidate_version: str
    baseline_trace_id: str | None = None
    candidate_trace_id: str | None = None
    behavioral_matrix: dict[str, Any]
    disclaimer: str
