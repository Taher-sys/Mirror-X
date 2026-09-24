"""Reality Graph Node and Edge models."""

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel


class GraphNode(BaseModel):
    """A node in the Reality Graph representing an architectural entity."""

    __tablename__ = "graph_nodes"

    node_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    outbound_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    inbound_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GraphNode [{self.node_type}] {self.name}>"


class GraphEdge(BaseModel):
    """A directed edge in the Reality Graph representing a relationship between entities."""

    __tablename__ = "graph_edges"

    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    source_node: Mapped["GraphNode"] = relationship(
        "GraphNode",
        foreign_keys=[source_node_id],
        back_populates="outbound_edges",
    )
    target_node: Mapped["GraphNode"] = relationship(
        "GraphNode",
        foreign_keys=[target_node_id],
        back_populates="inbound_edges",
    )

    def __repr__(self) -> str:
        return f"<GraphEdge {self.relationship_type}: {self.source_node_id} -> {self.target_node_id}>"
