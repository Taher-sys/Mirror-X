"""Activity schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActivityBase(BaseModel):
    """Base activity schema."""

    actor: str = Field("system", max_length=100)
    action: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_name: str = Field(..., min_length=1, max_length=255)
    details: str | None = None
    metadata_payload: dict[str, Any] | None = None


class ActivityCreate(ActivityBase):
    """Schema for recording an activity."""


class ActivityResponse(ActivityBase):
    """Schema for activity responses."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
