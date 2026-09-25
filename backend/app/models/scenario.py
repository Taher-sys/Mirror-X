"""Synthetic Scenario Engine database model."""

from typing import Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ScenarioRecord(BaseModel):
    """Represents a reproducible synthetic test scenario generated from APIs, schemas, or policies."""

    __tablename__ = "scenarios"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scenario_class: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # normal, boundary, incomplete, malformed, contradictory, unauthorized, adversarial, outage, tool_failure, ambiguous
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # api, schema, domain_model, policy, tool_definition, validation_rule, existing_test
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)

    initial_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    generated_inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expected_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    participating_resources: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    applicable_policies: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)
    execution_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<ScenarioRecord {self.name} [{self.scenario_class}] seed={self.seed}>"
