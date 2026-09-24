"""Repository schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryBase(BaseModel):
    """Base repository schema."""

    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=1024)
    default_branch: str = Field("main", max_length=100)
    language: str | None = Field(None, max_length=100)
    status: str = Field("active", max_length=50)


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository."""

    project_id: uuid.UUID


class RepositoryResponse(RepositoryBase):
    """Schema for repository responses."""

    id: uuid.UUID
    project_id: uuid.UUID
    services_count: int = 0
    findings_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
