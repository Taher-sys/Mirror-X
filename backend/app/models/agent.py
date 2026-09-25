"""Agent Behavior Lab models: Agent, AgentTool, AgentRun, and AgentStep."""

import uuid
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel


class Agent(BaseModel):
    """An AI agent definition under evaluation."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0.0", index=True)
    model_reference: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o")
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    config_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.version}) [{self.model_reference}]>"


class AgentTool(BaseModel):
    """A tool available for agents to invoke in the controlled sandbox."""

    __tablename__ = "agent_tools"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), default="read", nullable=False)  # read, write, sensitive
    is_mock_safe: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AgentTool {self.name} risk={self.risk_level}>"


class AgentRun(BaseModel):
    """Execution telemetry record of an Agent solving a goal."""

    __tablename__ = "agent_runs"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_version: Mapped[str] = mapped_column(String(50), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    context_reference: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    model_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    plan: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # completed, failed, policy_blocked, aborted
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    timings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Measurable behavior metrics (Explicitly NO arbitrary single "intelligence score")
    successful_completion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    correct_tool_selection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_tool_use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unnecessary_actions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policy_violations_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")
    steps: Mapped[list["AgentStep"]] = relationship(
        "AgentStep",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentStep.step_number",
    )

    def __repr__(self) -> str:
        return f"<AgentRun trace={self.trace_id} status={self.status}>"


class AgentStep(BaseModel):
    """An individual discrete step/action within an AgentRun."""

    __tablename__ = "agent_steps"

    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    thought: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tool_call: Mapped[str | None] = mapped_column(String(100), nullable=True)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    tool_output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    policy_check: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)  # success, tool_error, policy_denied, unnecessary
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="steps")

    def __repr__(self) -> str:
        return f"<AgentStep run={self.run_id} step={self.step_number} tool={self.tool_call}>"
