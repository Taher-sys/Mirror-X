"""Normalized types for repository ingestion and Reality Graph construction."""

from dataclasses import dataclass, field
from typing import Any, Literal

NodeType = Literal[
    "repository",
    "service",
    "component",
    "api",
    "database",
    "table",
    "deployment",
    "documentation",
]

RelationshipType = Literal[
    "contains",
    "depends_on",
    "calls",
    "reads_from",
    "writes_to",
    "deployed_as",
    "documents",
]


@dataclass
class ParsedNode:
    """Normalized domain entity extracted during repository ingestion."""

    name: str
    node_type: NodeType
    path: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedEdge:
    """Directed relationship between domain entities."""

    source_name: str
    source_type: NodeType
    target_name: str
    target_type: NodeType
    relationship_type: RelationshipType
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionResult:
    """Consolidated output of repository parsing."""

    nodes: list[ParsedNode] = field(default_factory=list)
    edges: list[ParsedEdge] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
