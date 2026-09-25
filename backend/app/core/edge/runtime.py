"""Edge Runtime Boundary and State Manager.

Maintains demonstrable ONLINE/OFFLINE network modes, enforces capability constraints,
and routes local-first execution.
"""

from datetime import datetime
from typing import Any
import uuid

from app.core.errors import AppException


PERMITTED_OFFLINE_CAPABILITIES = {
    "local_metadata",
    "graph_exploration",
    "policy_evaluation",
    "scenario_execution",
    "agent_evaluation",
    "local_evidence_creation",
    "trace_storage",
    "sync_queue_management",
}

UNAVAILABLE_CLOUD_CAPABILITIES = {
    "cloud_model_training": "Model training and deep learning experiments require centralized compute infrastructure and full historical telemetry.",
    "global_release_passport": "Authoritative cryptographic Release Passports require global verification across all organizations and environments.",
    "repository_ingestion": "Ingesting and parsing multi-format external source code repositories is reserved for the primary cloud ingestion engine.",
    "central_analytics": "Aggregated cross-tenant metrics and historical trend analytics require cloud warehouse access.",
}

from fastapi import HTTPException


class OfflineCapabilityError(HTTPException):
    """Raised when an operation requiring cloud connectivity is attempted in offline mode."""

    def __init__(self, capability: str, reason: str | None = None) -> None:
        explanation = reason or UNAVAILABLE_CLOUD_CAPABILITIES.get(
            capability,
            "This operation requires active cloud connectivity.",
        )
        msg = (
            f"Operation '{capability}' is unavailable in OFFLINE mode: {explanation} "
            f"Permitted offline operations: {', '.join(sorted(PERMITTED_OFFLINE_CAPABILITIES))}."
        )
        super().__init__(status_code=503, detail=msg)


class EdgeRuntimeManager:
    """Manages demonstrable edge node operational state, network modes, and capability checks."""

    _instance: "EdgeRuntimeManager | None" = None

    def __new__(cls) -> "EdgeRuntimeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self) -> None:
        self.node_id = str(uuid.uuid4())
        self.network_mode: str = "ONLINE"  # ONLINE or OFFLINE
        self.sync_status: str = "idle"  # idle, syncing, offline, conflict_detected
        self.last_sync_timestamp: datetime | None = None
        self.active_snapshot_version: str = "v1.0-cloud-snapshot"
        self.local_stats: dict[str, int] = {
            "cached_nodes": 0,
            "cached_edges": 0,
            "cached_policies": 0,
            "pending_sync_events": 0,
            "recorded_conflicts": 0,
        }

    def set_network_mode(self, mode: str) -> str:
        """Set network connectivity state ('ONLINE' or 'OFFLINE')."""
        mode_upper = mode.upper()
        if mode_upper not in ("ONLINE", "OFFLINE"):
            raise ValueError(f"Invalid network mode '{mode}'. Must be 'ONLINE' or 'OFFLINE'.")
        self.network_mode = mode_upper
        if self.network_mode == "OFFLINE":
            self.sync_status = "offline"
        else:
            if self.sync_status == "offline":
                self.sync_status = "idle"
        return self.network_mode

    def assert_capability(self, capability: str) -> None:
        """Verify whether an operation is permitted under current network connectivity."""
        if self.network_mode == "OFFLINE":
            if capability not in PERMITTED_OFFLINE_CAPABILITIES:
                reason = UNAVAILABLE_CLOUD_CAPABILITIES.get(capability)
                raise OfflineCapabilityError(capability, reason)

    def get_status_payload(self) -> dict[str, Any]:
        """Compile a complete status payload of the edge node runtime."""
        return {
            "node_id": self.node_id,
            "network_mode": self.network_mode,
            "sync_status": self.sync_status,
            "active_snapshot_version": self.active_snapshot_version,
            "last_sync_timestamp": self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None,
            "is_offline": self.network_mode == "OFFLINE",
            "local_stats": self.local_stats,
            "permitted_offline_capabilities": sorted(list(PERMITTED_OFFLINE_CAPABILITIES)),
            "restricted_cloud_capabilities": list(UNAVAILABLE_CLOUD_CAPABILITIES.keys()),
        }


def get_edge_runtime() -> EdgeRuntimeManager:
    """Access the singleton EdgeRuntimeManager instance."""
    return EdgeRuntimeManager()
