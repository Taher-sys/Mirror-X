"""Pydantic schemas for MIRROR-X Edge and Local-First Runtime."""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class EdgeStatusResponse(BaseModel):
    """Complete health and connectivity status of the Edge node."""

    node_id: str
    network_mode: str  # ONLINE or OFFLINE
    sync_status: str  # idle, syncing, offline, conflict_detected
    active_snapshot_version: str
    last_sync_timestamp: str | None = None
    is_offline: bool
    local_stats: dict[str, int]
    permitted_offline_capabilities: list[str]
    restricted_cloud_capabilities: list[str]


class NetworkModeToggleRequest(BaseModel):
    """Request to transition edge node network connectivity mode."""

    network_mode: str = Field(..., description="'ONLINE' or 'OFFLINE'")


class SnapshotPullResponse(BaseModel):
    """Result of pulling an authoritative signed cloud snapshot."""

    snapshot_version: str
    nodes_loaded: int
    edges_loaded: int
    policies_loaded: int
    signature: str


class SyncQueueItem(BaseModel):
    """Item in the outbound synchronization queue."""

    id: str
    source: str
    timestamp: datetime
    entity_type: str
    entity_id: str
    version: int
    payload: dict[str, Any]
    checksum: str
    status: str
    retry_count: int
    last_error: str | None = None


class SyncFlushResponse(BaseModel):
    """Outcome of flushing the outbound queue to the cloud."""

    status: str
    events_processed: int
    synced_count: int
    duplicate_count: int
    conflict_count: int
    sync_status: str


class EdgeConflictResponse(BaseModel):
    """Explicit record of conflicting concurrent modifications."""

    id: str
    entity_type: str
    entity_id: str
    local_event_id: str
    local_version: int
    remote_version: int
    local_payload: dict[str, Any]
    remote_payload: dict[str, Any]
    resolution_status: str
    resolution_notes: str | None = None
    detected_at: datetime


class ConflictResolveRequest(BaseModel):
    """Action to resolve an explicit sync conflict."""

    resolution: str = Field(..., description="'keep_local' or 'accept_remote'")
    notes: str | None = Field(None, description="Optional rationale for resolution")


class EdgeLocalEvidenceCreateRequest(BaseModel):
    """Payload to create an evidence record directly on the edge."""

    evidence_type: str = Field("local_edge_observation", description="Type of evidence")
    source_reference: str = Field(..., description="Unique source path or reference")
    summary: str = Field(..., description="Summary of evidence")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Structured evidence payload")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence rating")
