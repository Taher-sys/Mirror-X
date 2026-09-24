"""Reality Graph API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.errors import AppException
from app.core.ingestion.engine import IngestionEngine
from app.models.graph import GraphEdge, GraphNode
from app.schemas.common import StandardResponse
from app.schemas.graph import (
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphRetrievalResponse,
    GraphStatisticsResponse,
    IngestionResponse,
    IngestRepositoryRequest,
)

router = APIRouter(prefix="/graph", tags=["Reality Graph"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
ingestion_engine = IngestionEngine()


@router.post("/ingest", response_model=StandardResponse[IngestionResponse], status_code=status.HTTP_201_CREATED)
async def ingest_repository(
    payload: IngestRepositoryRequest,
    db: DatabaseSession,
) -> StandardResponse[IngestionResponse]:
    """Ingest software repository files into the Reality Graph."""
    parsed_result = ingestion_engine.ingest_files_dict(
        repo_name=payload.repository_name,
        files=payload.files,
    )

    stats = await ingestion_engine.persist_graph(
        db=db,
        repository_id=payload.repository_id,
        repo_name=payload.repository_name,
        result=parsed_result,
    )

    return StandardResponse(data=IngestionResponse(**stats))


@router.get("", response_model=StandardResponse[GraphRetrievalResponse])
async def get_graph(
    db: DatabaseSession,
    repository_id: Annotated[uuid.UUID | None, Query(description="Filter by repository ID")] = None,
    node_type: Annotated[str | None, Query(description="Filter by node type")] = None,
    search: Annotated[str | None, Query(description="Search node name")] = None,
) -> StandardResponse[GraphRetrievalResponse]:
    """Retrieve Reality Graph nodes and directed relationships."""
    node_query = select(GraphNode)

    if repository_id:
        node_query = node_query.where(GraphNode.repository_id == repository_id)
    if node_type:
        node_query = node_query.where(GraphNode.node_type == node_type.lower())
    if search:
        node_query = node_query.where(GraphNode.name.ilike(f"%{search}%"))

    node_res = await db.execute(node_query)
    nodes = node_res.scalars().all()
    node_ids = {n.id for n in nodes}

    # Fetch edges connected to retrieved nodes
    edges: list[GraphEdge] = []
    if node_ids:
        edge_query = (
            select(GraphEdge)
            .options(selectinload(GraphEdge.source_node), selectinload(GraphEdge.target_node))
            .where(
                (GraphEdge.source_node_id.in_(node_ids)) & (GraphEdge.target_node_id.in_(node_ids))
            )
        )
        edge_res = await db.execute(edge_query)
        edges = list(edge_res.scalars().all())

    node_items = [
        GraphNodeResponse(
            id=n.id,
            node_type=n.node_type,
            name=n.name,
            path=n.path,
            properties=n.properties,
            repository_id=n.repository_id,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in nodes
    ]

    edge_items = [
        GraphEdgeResponse(
            id=e.id,
            relationship_type=e.relationship_type,
            properties=e.properties,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            source_node_name=e.source_node.name if e.source_node else None,
            source_node_type=e.source_node.node_type if e.source_node else None,
            target_node_name=e.target_node.name if e.target_node else None,
            target_node_type=e.target_node.node_type if e.target_node else None,
            created_at=e.created_at,
        )
        for e in edges
    ]

    data = GraphRetrievalResponse(
        nodes=node_items,
        edges=edge_items,
        total_nodes=len(node_items),
        total_edges=len(edge_items),
    )
    return StandardResponse(data=data)


@router.get("/statistics", response_model=StandardResponse[GraphStatisticsResponse])
async def get_graph_statistics(db: DatabaseSession) -> StandardResponse[GraphStatisticsResponse]:
    """Calculate aggregated Reality Graph topological statistics."""
    total_nodes_res = await db.execute(select(func.count(GraphNode.id)))
    total_nodes = total_nodes_res.scalar() or 0

    total_edges_res = await db.execute(select(func.count(GraphEdge.id)))
    total_edges = total_edges_res.scalar() or 0

    # Nodes grouped by type
    type_res = await db.execute(
        select(GraphNode.node_type, func.count(GraphNode.id)).group_by(GraphNode.node_type)
    )
    nodes_by_type = {row[0]: row[1] for row in type_res.fetchall()}

    # Edges grouped by relationship
    rel_res = await db.execute(
        select(GraphEdge.relationship_type, func.count(GraphEdge.id)).group_by(GraphEdge.relationship_type)
    )
    edges_by_rel = {row[0]: row[1] for row in rel_res.fetchall()}

    # Density = |E| / (|V|*(|V|-1)) for directed graphs
    density = 0.0
    if total_nodes > 1:
        density = round(total_edges / (total_nodes * (total_nodes - 1)), 4)

    data = GraphStatisticsResponse(
        total_nodes=total_nodes,
        total_edges=total_edges,
        nodes_by_type=nodes_by_type,
        edges_by_relationship=edges_by_rel,
        graph_density=density,
    )
    return StandardResponse(data=data)


@router.get("/nodes/{node_id}", response_model=StandardResponse[GraphNodeResponse])
async def get_node_details(
    node_id: uuid.UUID,
    db: DatabaseSession,
) -> StandardResponse[GraphNodeResponse]:
    """Retrieve detailed properties for a single Reality Graph node."""
    node = await db.get(GraphNode, node_id)
    if not node:
        raise AppException(
            code="NODE_NOT_FOUND",
            message=f"Graph node with ID '{node_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return StandardResponse(
        data=GraphNodeResponse(
            id=node.id,
            node_type=node.node_type,
            name=node.name,
            path=node.path,
            properties=node.properties,
            repository_id=node.repository_id,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
    )


@router.get("/relationships", response_model=StandardResponse[list[GraphEdgeResponse]])
async def list_relationships(
    db: DatabaseSession,
    relationship_type: Annotated[str | None, Query(description="Filter by relationship type")] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Items limit")] = 100,
) -> StandardResponse[list[GraphEdgeResponse]]:
    """List Reality Graph relationships and link details."""
    query = select(GraphEdge).options(
        selectinload(GraphEdge.source_node), selectinload(GraphEdge.target_node)
    )

    if relationship_type:
        query = query.where(GraphEdge.relationship_type == relationship_type.lower())

    query = query.order_by(GraphEdge.created_at.desc()).limit(limit)
    res = await db.execute(query)
    edges = res.scalars().all()

    items = [
        GraphEdgeResponse(
            id=e.id,
            relationship_type=e.relationship_type,
            properties=e.properties,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            source_node_name=e.source_node.name if e.source_node else None,
            source_node_type=e.source_node.node_type if e.source_node else None,
            target_node_name=e.target_node.name if e.target_node else None,
            target_node_type=e.target_node.node_type if e.target_node else None,
            created_at=e.created_at,
        )
        for e in edges
    ]

    return StandardResponse(data=items)
