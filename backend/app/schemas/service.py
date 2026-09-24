"""Service schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    """Base service schema."""

    name: str = Field(..., min_length=1, max_length=255)
    service_type: str = Field("api", max_length=50)
    status: str = Field("healthy", max_length=50)
    runtime: str | None = Field(None, max_length=100)
    version: str = Field("v1.0.0", max_length=50)


class ServiceCreate(ServiceBase):
    """Schema for registering a service."""

    repository_id: uuid.UUID


class ServiceResponse(ServiceBase):
    """Schema for service responses."""

    id: uuid.UUID
    repository_id: uuid.UUID
    repository_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
