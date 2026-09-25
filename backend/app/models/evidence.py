"""Evidence Ledger model for tamper-evident provenance records."""

import hashlib
import json
from typing import Any

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EvidenceRecord(BaseModel):
    """An immutable, verifiable evidence record supporting an analytical conclusion or decision."""

    __tablename__ = "evidence_records"

    evidence_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # source_file, graph_relationship, api_contract, test_execution, scenario_run, agent_execution, policy_decision, runtime_trace
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    hash_signature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    linked_finding_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    linked_change_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    @classmethod
    def calculate_hash(cls, raw_payload: dict[str, Any], source_reference: str) -> str:
        """Compute deterministic SHA-256 hash over payload and source reference."""
        serialized = json.dumps({"source": source_reference, "payload": raw_payload}, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"<EvidenceRecord {self.evidence_type} [{self.source_reference}] hash={self.hash_signature[:8]}...>"
