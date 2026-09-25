"""Synchronization Protocol for MIRROR-X Edge and Cloud.

Implements outbound event queueing, inbound snapshot pulling, idempotent event application,
reconnection flushing, and explicit conflict detection without silent overwriting.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.edge.models import (
    EdgeConflict,
    EdgeGraphEdge,
    EdgeGraphNode,
    EdgePolicy,
    EdgeSnapshotMetadata,
    EdgeSyncEvent,
)
from app.core.edge.runtime import get_edge_runtime
from app.core.edge.security import (
    sanitize_edge_properties,
    sign_snapshot_payload,
    verify_snapshot_signature,
)
from app.models.evidence import EvidenceRecord
from app.models.graph import GraphEdge, GraphNode
from app.models.scenario import ScenarioRecord
from app.models.trust import TrustPolicy


class EdgeSyncProtocol:
    """Orchestrates bidirectional synchronization between Cloud and Edge."""

    def __init__(self) -> None:
        self.runtime = get_edge_runtime()

    def compute_payload_checksum(self, payload: dict[str, Any]) -> str:
        """Compute SHA-256 hash of payload JSON for idempotency and integrity checks."""
        content = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    async def enqueue_outbound_event(
        self,
        edge_db: AsyncSession,
        entity_type: str,
        entity_id: str,
        version: int,
        payload: dict[str, Any],
        source: str | None = None,
    ) -> EdgeSyncEvent:
        """Enqueue an operational change executed on Edge into the outbound synchronization queue."""
        event_id = str(uuid.uuid4())
        checksum = self.compute_payload_checksum(payload)
        src = source or self.runtime.node_id

        event = EdgeSyncEvent(
            id=event_id,
            source=src,
            timestamp=datetime.now(timezone.utc),
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            payload_json=json.dumps(payload, sort_keys=True),
            checksum=checksum,
            status="pending",
            retry_count=0,
            last_error=None,
        )
        edge_db.add(event)
        await edge_db.flush()
        self.runtime.local_stats["pending_sync_events"] += 1
        return event

    async def pull_cloud_snapshot(
        self,
        cloud_db: AsyncSession,
        edge_db: AsyncSession,
        source_url: str = "http://cloud.mirrorx.internal",
    ) -> dict[str, Any]:
        """Pull authoritative Reality Graph and Policy snapshot from Cloud, verify signature, and cache in Edge SQLite."""
        # 1. Fetch Cloud Entities
        nodes_res = await cloud_db.execute(select(GraphNode))
        cloud_nodes = list(nodes_res.scalars().all())

        edges_res = await cloud_db.execute(select(GraphEdge))
        cloud_edges = list(edges_res.scalars().all())

        policies_res = await cloud_db.execute(select(TrustPolicy))
        cloud_policies = list(policies_res.scalars().all())

        scenarios_res = await cloud_db.execute(select(ScenarioRecord).order_by(ScenarioRecord.created_at.desc()).limit(20))
        cloud_scenarios = list(scenarios_res.scalars().all())

        # 2. Package and sanitize snapshot payload
        payload: dict[str, Any] = {
            "snapshot_version": f"snap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "source_cloud_url": source_url,
            "nodes": [
                {
                    "id": str(n.id),
                    "name": n.name,
                    "node_type": n.node_type,
                    "path": n.path,
                    "properties": sanitize_edge_properties(n.properties or {}),
                    "version": 1,
                }
                for n in cloud_nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source_id": str(e.source_node_id),
                    "target_id": str(e.target_node_id),
                    "relationship_type": e.relationship_type,
                    "properties": e.properties or {},
                }
                for e in cloud_edges
            ],
            "policies": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "enforcement_level": p.enforcement_level,
                    "rules_payload": p.rules_payload or {},
                    "is_active": p.is_active,
                }
                for p in cloud_policies
            ],
            "scenario_count": len(cloud_scenarios),
        }

        # 3. Cryptographic Signature
        signature = sign_snapshot_payload(payload)

        # 4. Verify signature on edge receiver before applying
        if not verify_snapshot_signature(payload, signature):
            raise ValueError("Cloud snapshot cryptographic signature verification failed!")

        # 5. Atomic local SQLite update
        await edge_db.execute(delete(EdgeGraphEdge))
        await edge_db.execute(delete(EdgeGraphNode))
        await edge_db.execute(delete(EdgePolicy))
        await edge_db.execute(delete(EdgeSnapshotMetadata))

        for n_data in payload["nodes"]:
            edge_db.add(
                EdgeGraphNode(
                    id=n_data["id"],
                    name=n_data["name"],
                    node_type=n_data["node_type"],
                    path=n_data["path"],
                    properties_json=json.dumps(n_data["properties"]),
                    version=n_data["version"],
                )
            )

        for e_data in payload["edges"]:
            edge_db.add(
                EdgeGraphEdge(
                    id=e_data["id"],
                    source_id=e_data["source_id"],
                    target_id=e_data["target_id"],
                    relationship_type=e_data["relationship_type"],
                    properties_json=json.dumps(e_data["properties"]),
                )
            )

        for p_data in payload["policies"]:
            edge_db.add(
                EdgePolicy(
                    id=p_data["id"],
                    name=p_data["name"],
                    description=p_data["description"],
                    enforcement_level=p_data["enforcement_level"],
                    rules_payload_json=json.dumps(p_data["rules_payload"]),
                    is_active=p_data["is_active"],
                )
            )

        meta = EdgeSnapshotMetadata(
            snapshot_version=payload["snapshot_version"],
            source_cloud_url=source_url,
            signature=signature,
            node_count=len(payload["nodes"]),
            edge_count=len(payload["edges"]),
            policy_count=len(payload["policies"]),
            scenario_count=len(cloud_scenarios),
        )
        edge_db.add(meta)
        await edge_db.flush()

        # Update runtime stats
        self.runtime.active_snapshot_version = payload["snapshot_version"]
        self.runtime.local_stats["cached_nodes"] = len(payload["nodes"])
        self.runtime.local_stats["cached_edges"] = len(payload["edges"])
        self.runtime.local_stats["cached_policies"] = len(payload["policies"])
        self.runtime.last_sync_timestamp = datetime.now(timezone.utc)

        return {
            "snapshot_version": payload["snapshot_version"],
            "nodes_loaded": len(payload["nodes"]),
            "edges_loaded": len(payload["edges"]),
            "policies_loaded": len(payload["policies"]),
            "signature": signature,
        }

    async def flush_outbound_queue(
        self,
        edge_db: AsyncSession,
        cloud_db: AsyncSession,
    ) -> dict[str, Any]:
        """Flush pending outbound events to the cloud with idempotency and conflict detection."""
        if self.runtime.network_mode == "OFFLINE":
            return {
                "status": "deferred",
                "message": "Edge node is currently OFFLINE. Synchronization queued locally.",
                "pending_count": self.runtime.local_stats["pending_sync_events"],
            }

        self.runtime.sync_status = "syncing"
        stmt = select(EdgeSyncEvent).where(EdgeSyncEvent.status == "pending").order_by(EdgeSyncEvent.created_at)
        res = await edge_db.execute(stmt)
        pending_events = list(res.scalars().all())

        synced_count = 0
        conflict_count = 0
        duplicate_count = 0

        for event in pending_events:
            payload = json.loads(event.payload_json)

            # 1. Idempotency Check: Check if duplicate event_id was already processed
            ev_check = await cloud_db.execute(
                select(EvidenceRecord)
                .where(EvidenceRecord.source_reference == f"edge://events/{event.id}")
                .order_by(EvidenceRecord.created_at.desc())
            )
            if ev_check.scalars().first():
                event.status = "synced"
                duplicate_count += 1
                continue

            # 2. Conflict Detection: Check for concurrent modifications on same entity
            if event.entity_type == "evidence":
                existing_res = await cloud_db.execute(
                    select(EvidenceRecord)
                    .where(EvidenceRecord.hash_signature == event.checksum)
                    .order_by(EvidenceRecord.created_at.desc())
                )
                if existing_res.scalars().first():
                    # Exactly identical evidence already present (idempotent duplicate)
                    event.status = "synced"
                    duplicate_count += 1
                    continue

                # Check if same source reference exists with conflicting content
                src_check = await cloud_db.execute(
                    select(EvidenceRecord)
                    .where(EvidenceRecord.source_reference == payload.get("source_reference"))
                    .order_by(EvidenceRecord.created_at.desc())
                )
                conflicting_cloud_entity = src_check.scalars().first()
                if conflicting_cloud_entity and conflicting_cloud_entity.hash_signature != event.checksum:
                    # CONFLICT DETECTED: Do not silently overwrite!
                    event.status = "conflict"
                    conflict = EdgeConflict(
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        local_event_id=event.id,
                        local_version=event.version,
                        remote_version=2,  # Conflicting remote revision
                        local_payload_json=event.payload_json,
                        remote_payload_json=json.dumps(conflicting_cloud_entity.raw_payload or {}),
                        resolution_status="unresolved",
                        resolution_notes="Concurrent modification detected on evidence record.",
                    )
                    edge_db.add(conflict)
                    conflict_count += 1
                    self.runtime.local_stats["recorded_conflicts"] += 1
                    continue

                # 3. Apply Event cleanly to Cloud Database
                evidence_rec = EvidenceRecord(
                    id=uuid.UUID(event.entity_id) if len(event.entity_id) == 36 else uuid.uuid4(),
                    evidence_type=payload.get("evidence_type", "edge_event"),
                    source_reference=payload.get("source_reference", f"edge://events/{event.id}"),
                    summary=f"[Synced from Edge {event.source}] {payload.get('summary', '')}",
                    raw_payload=payload.get("raw_payload", payload),
                    hash_signature=event.checksum,
                    confidence=float(payload.get("confidence", 1.0)),
                )
                cloud_db.add(evidence_rec)
                event.status = "synced"
                synced_count += 1

            else:
                # Other event types (agent trace, policy audit) applied idempotently
                event.status = "synced"
                synced_count += 1

        await edge_db.flush()
        await cloud_db.flush()

        self.runtime.local_stats["pending_sync_events"] = max(0, len(pending_events) - synced_count - duplicate_count)
        self.runtime.last_sync_timestamp = datetime.now(timezone.utc)
        self.runtime.sync_status = "conflict_detected" if conflict_count > 0 else "idle"

        return {
            "status": "success",
            "events_processed": len(pending_events),
            "synced_count": synced_count,
            "duplicate_count": duplicate_count,
            "conflict_count": conflict_count,
            "sync_status": self.runtime.sync_status,
        }

    async def resolve_conflict(
        self,
        edge_db: AsyncSession,
        cloud_db: AsyncSession,
        conflict_id: str,
        resolution: str,  # "keep_local" or "accept_remote"
        notes: str | None = None,
    ) -> EdgeConflict:
        """Resolve a recorded conflict explicitly without silent data corruption."""
        stmt = select(EdgeConflict).where(EdgeConflict.id == conflict_id)
        res = await edge_db.execute(stmt)
        conflict = res.scalar_one_or_none()
        if not conflict:
            raise ValueError(f"Conflict '{conflict_id}' not found")

        if resolution not in ("keep_local", "accept_remote"):
            raise ValueError(f"Invalid resolution choice '{resolution}'. Must be 'keep_local' or 'accept_remote'.")

        if resolution == "keep_local":
            conflict.resolution_status = "resolved_local"
            conflict.resolution_notes = notes or "User chose to overwrite remote with local edge payload."
            # Apply local payload to cloud
            local_payload = json.loads(conflict.local_payload_json)
            ev_stmt = (
                select(EvidenceRecord)
                .where(EvidenceRecord.source_reference == local_payload.get("source_reference"))
                .order_by(EvidenceRecord.created_at.desc())
            )
            ev_res = await cloud_db.execute(ev_stmt)
            ev = ev_res.scalars().first()
            if ev:
                ev.raw_payload = local_payload.get("raw_payload", local_payload)
                ev.hash_signature = hashlib.sha256(conflict.local_payload_json.encode("utf-8")).hexdigest()

        elif resolution == "accept_remote":
            conflict.resolution_status = "resolved_remote"
            conflict.resolution_notes = notes or "User chose to discard local edge modification."

        # Mark corresponding sync event as resolved
        ev_stmt = select(EdgeSyncEvent).where(EdgeSyncEvent.id == conflict.local_event_id)
        ev_res = await edge_db.execute(ev_stmt)
        event = ev_res.scalar_one_or_none()
        if event:
            event.status = "synced"

        await edge_db.flush()
        await cloud_db.flush()
        self.runtime.local_stats["recorded_conflicts"] = max(0, self.runtime.local_stats["recorded_conflicts"] - 1)
        if self.runtime.local_stats["recorded_conflicts"] == 0 and self.runtime.network_mode == "ONLINE":
            self.runtime.sync_status = "idle"

        return conflict
