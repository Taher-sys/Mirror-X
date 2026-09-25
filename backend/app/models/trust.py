"""Trust Layer models: Principal, Resource, Action, Permission, Policy, and PolicyDecision."""

from typing import Any

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Principal(BaseModel):
    """An identity entity invoking actions (user, service account, or autonomous agent)."""

    __tablename__ = "principals"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    principal_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="agent"
    )  # user, service_account, agent, system
    roles: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Principal {self.name} [{self.principal_type}]>"


class TrustResource(BaseModel):
    """A target resource protected by policy (sandbox/mock resources only - no production access)."""

    __tablename__ = "trust_resources"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # database, table, api_endpoint, repository, tool, file, sandbox_service
    classification: Mapped[str] = mapped_column(
        String(50),
        default="internal",
        nullable=False,
    )  # public, internal, confidential, restricted
    is_sandbox: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )  # Mandate: Must always be sandbox/mock!
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<TrustResource {self.name} [{self.resource_type}] sandbox={self.is_sandbox}>"


class TrustAction(BaseModel):
    """An operation attempted on a resource."""

    __tablename__ = "trust_actions"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )  # read, write, execute, delete, schema_alter, deploy
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    def __repr__(self) -> str:
        return f"<TrustAction {self.name} sensitive={self.is_sensitive}>"


class Permission(BaseModel):
    """Permission binding assigning action access on resource types."""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    principal_role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    effect: Mapped[str] = mapped_column(String(20), default="ALLOW", nullable=False)  # ALLOW, DENY
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Permission {self.name} {self.effect} {self.action_name} on {self.resource_type}>"


class TrustPolicy(BaseModel):
    """Governance rule evaluated by the Trust Layer engine."""

    __tablename__ = "trust_policies"

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_level: Mapped[str] = mapped_column(
        String(50), default="strict", nullable=False
    )  # strict, audit, advisory
    target_type: Mapped[str] = mapped_column(
        String(50), default="all", nullable=False
    )  # agent, principal, tool, resource
    rules_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<TrustPolicy {self.name} level={self.enforcement_level}>"


class PolicyDecision(BaseModel):
    """Record of an automated policy evaluation: ALLOW, DENY, or HUMAN_REVIEW_REQUIRED."""

    __tablename__ = "policy_decisions"

    principal_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # ALLOW, DENY, HUMAN_REVIEW_REQUIRED
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    matched_policies: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    context_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # approved, rejected

    def __repr__(self) -> str:
        return f"<PolicyDecision {self.action_name} on {self.resource_name} -> {self.result}>"
