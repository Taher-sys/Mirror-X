"""System telemetry and summary schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.finding import FindingSeverityCounts


class SystemStatusResponse(BaseModel):
    """Real system operational and database status."""

    status: str
    database_connected: bool
    database_dialect: str
    database_latency_ms: float
    api_version: str
    uptime_seconds: float
    timestamp: datetime
    active_connections: int = 1


class SystemSummaryResponse(BaseModel):
    """Real calculated system metrics from stored data."""

    repositories_count: int
    services_count: int
    findings_count: int
    findings_by_severity: FindingSeverityCounts
    services_healthy_count: int
    services_degraded_count: int
    system_status: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None
