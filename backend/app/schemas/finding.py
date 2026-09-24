"""Finding schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingBase(BaseModel):
    """Base finding schema."""

    title: str = Field(..., min_length=1, max_length=255)
    finding_type: str = Field(..., min_length=1, max_length=100)
    severity: str = Field("medium", max_length=50)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    description: str = Field(..., min_length=1)
    evidence_payload: dict[str, Any] | None = None
    status: str = Field("open", max_length=50)


class FindingCreate(FindingBase):
    """Schema for creating a finding."""

    repository_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None


class FindingResponse(FindingBase):
    """Schema for finding responses."""

    id: uuid.UUID
    repository_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None
    repository_name: str | None = None
    service_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FindingSeverityCounts(BaseModel):
    """Breakdown of findings count by severity."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0
