"""SQLAlchemy models for MIRROR-X Edge and Local-First Runtime."""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class EdgeBase(DeclarativeBase):
    """Declarative Base specifically for the SQLite Edge Runtime."""

    pass


class EdgeSnapshotMetadata(EdgeBase):
    """Metadata for the active cached cloud snapshot."""

    __tablename__ = "edge_snapshot_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_version: Mapped[str] = mapped_column(String(50), nullable=False)
    source_cloud_url: Mapped[str] = mapped_column(String(255), nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policy_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scenario_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class EdgeGraphNode(EdgeBase):
    """Local Reality Graph node replica."""

    __tablename__ = "edge_graph_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(512), default="/", nullable=False)
    properties_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class EdgeGraphEdge(EdgeBase):
    """Local Reality Graph relationship replica."""

    __tablename__ = "edge_graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    properties_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class EdgePolicy(EdgeBase):
    """Local Trust Layer policy replica."""

    __tablename__ = "edge_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_level: Mapped[str] = mapped_column(String(50), default="strict", nullable=False)
    rules_payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EdgeSyncEvent(EdgeBase):
    """Outbound synchronization queue item capturing local actions executed offline."""

    __tablename__ = "edge_sync_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # event_id
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)  # pending, synced, failed, conflict
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class EdgeConflict(EdgeBase):
    """Explicit record of conflicting concurrent state during synchronization."""

    __tablename__ = "edge_conflicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    local_event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    local_version: Mapped[int] = mapped_column(Integer, nullable=False)
    remote_version: Mapped[int] = mapped_column(Integer, nullable=False)
    local_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    remote_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), default="unresolved", nullable=False)  # unresolved, resolved_local, resolved_remote
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class EdgeEvidenceRecord(EdgeBase):
    """Local evidence records created during offline operations."""

    __tablename__ = "edge_evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    hash_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class EdgeAgentTrace(EdgeBase):
    """Local agent run traces recorded during offline operation."""

    __tablename__ = "edge_agent_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
