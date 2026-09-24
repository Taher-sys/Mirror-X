"""Reality Graph API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphNodeBase(BaseModel):
    """Base schema for a Reality Graph node."""

    node_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    path: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphNodeResponse(GraphNodeBase):
    """Response schema for a Reality Graph node."""

    id: uuid.UUID
    repository_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeBase(BaseModel):
    """Base schema for a Reality Graph edge."""

    relationship_type: str = Field(..., max_length=50)
    properties: dict[str, Any] = Field(default_factory=dict)
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID


class GraphEdgeResponse(GraphEdgeBase):
    """Response schema for a Reality Graph edge."""

    id: uuid.UUID
    source_node_name: str | None = None
    source_node_type: str | None = None
    target_node_name: str | None = None
    target_node_type: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphRetrievalResponse(BaseModel):
    """Full or filtered Reality Graph response for canvas rendering."""

    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    total_nodes: int
    total_edges: int


class GraphStatisticsResponse(BaseModel):
    """Aggregated Reality Graph topological metrics."""

    total_nodes: int
    total_edges: int
    nodes_by_type: dict[str, int]
    edges_by_relationship: dict[str, int]
    graph_density: float


class IngestRepositoryRequest(BaseModel):
    """Request payload to ingest files into the Reality Graph."""

    repository_id: uuid.UUID | None = None
    repository_name: str
    files: dict[str, str] = Field(
        ...,
        description="Dictionary mapping file paths to their string contents",
    )


class IngestionResponse(BaseModel):
    """Output summary of repository ingestion."""

    repository: str
    nodes_count: int
    edges_count: int
    warnings_count: int
