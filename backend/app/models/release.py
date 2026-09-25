"""Release and ReleasePassport models certifying ecosystem readiness."""

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel


class Release(BaseModel):
    """A release bundle candidate targeting an environment."""

    __tablename__ = "releases"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    target_environment: Mapped[str] = mapped_column(String(50), default="staging", nullable=False)
    commit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    change_ids: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, certified, rejected

    passport: Mapped["ReleasePassport | None"] = relationship(
        "ReleasePassport",
        back_populates="release",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Release {self.version} ({self.name}) [{self.target_environment}]>"


class ReleasePassport(BaseModel):
    """Verifiable cryptographic passport summarizing testing, policy, and evidence completeness."""

    __tablename__ = "release_passports"

    release_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("releases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    overall_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NOT_EVALUATED",
    )  # PASS, FAIL, WARNING, HUMAN_REVIEW_REQUIRED, NOT_EVALUATED

    code_change_analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    context_findings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    scenario_testing: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    agent_testing: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    policy_validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evidence_completeness: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    uncertainty_notes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )  # Transparently declares unverified gaps without fabricating metrics
    passport_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    release: Mapped["Release"] = relationship("Release", back_populates="passport")

    @classmethod
    def calculate_seal(cls, release_version: str, sections: dict[str, Any]) -> str:
        """Compute cryptographic SHA-256 seal for the release passport."""
        serialized = json.dumps({"version": release_version, "sections": sections}, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"<ReleasePassport release={self.release_id} status={self.overall_status}>"
