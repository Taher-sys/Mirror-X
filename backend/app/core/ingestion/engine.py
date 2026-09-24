"""Ingestion engine orchestrating file parsers and persisting the Reality Graph."""

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ingestion.parsers.docker_compose import parse_docker_compose
from app.core.ingestion.parsers.dockerfile import parse_dockerfile
from app.core.ingestion.parsers.kubernetes import parse_kubernetes
from app.core.ingestion.parsers.markdown import parse_markdown
from app.core.ingestion.parsers.openapi import parse_openapi
from app.core.ingestion.parsers.package_json import parse_package_json
from app.core.ingestion.parsers.pyproject import parse_pyproject_toml
from app.core.ingestion.parsers.requirements import parse_requirements_txt
from app.core.ingestion.parsers.sql_schema import parse_sql_schema
from app.core.ingestion.parsers.terraform import parse_terraform
from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode
from app.models.activity import Activity
from app.models.graph import GraphEdge, GraphNode


class IngestionEngine:
    """Orchestrates multi-format repository parsing and Reality Graph persistence."""

    def parse_file(self, filename: str, content: str) -> IngestionResult:
        """Route file content to appropriate parser based on filename conventions."""
        lower_name = Path(filename).name.lower()

        if lower_name == "package.json":
            return parse_package_json(content, filename)
        elif lower_name == "pyproject.toml":
            return parse_pyproject_toml(content, filename)
        elif "requirements" in lower_name and lower_name.endswith(".txt"):
            return parse_requirements_txt(content, filename)
        elif lower_name == "dockerfile" or lower_name.endswith(".dockerfile"):
            return parse_dockerfile(content, filename)
        elif "docker-compose" in lower_name and lower_name.endswith((".yml", ".yaml")):
            return parse_docker_compose(content, filename)
        elif ("openapi" in lower_name or "swagger" in lower_name) and lower_name.endswith((".json", ".yaml", ".yml")):
            return parse_openapi(content, filename)
        elif lower_name.endswith(".sql"):
            return parse_sql_schema(content, filename)
        elif lower_name.endswith((".md", ".markdown")):
            return parse_markdown(content, filename)
        elif lower_name.endswith(".tf"):
            return parse_terraform(content, filename)
        elif lower_name.endswith((".yaml", ".yml")) and any(kw in lower_name for kw in ("k8s", "deploy", "pod", "ingress")):
            return parse_kubernetes(content, filename)
        else:

            res = IngestionResult()
            res.warnings.append(f"No specialized parser matched for '{filename}'")
            return res

    def ingest_files_dict(self, repo_name: str, files: dict[str, str]) -> IngestionResult:
        """Parse in-memory dictionary of {filename: content} and assemble Reality Graph."""
        consolidated = IngestionResult()

        # Add top-level repository node
        repo_node = ParsedNode(
            name=repo_name,
            node_type="repository",
            path="/",
            properties={"total_files": len(files)},
        )
        consolidated.nodes.append(repo_node)

        for filename, content in files.items():
            file_result = self.parse_file(filename, content)
            consolidated.nodes.extend(file_result.nodes)
            consolidated.edges.extend(file_result.edges)
            consolidated.warnings.extend(file_result.warnings)

        # Connect repository to top-level services, databases, and docs with `contains`
        for node in consolidated.nodes:
            if node.node_type in ("service", "database", "documentation") and node.name != repo_name:
                consolidated.edges.append(
                    ParsedEdge(
                        source_name=repo_name,
                        source_type="repository",
                        target_name=node.name,
                        target_type=node.node_type,
                        relationship_type="contains",
                    )
                )

        return consolidated

    async def persist_graph(
        self,
        db: AsyncSession,
        repository_id: uuid.UUID | None,
        repo_name: str,
        result: IngestionResult,
    ) -> dict[str, Any]:
        """Persist parsed nodes and edges into the database, resolving relationships."""
        # If repository_id provided, clear previous graph for clean re-ingestion
        if repository_id:
            await db.execute(
                delete(GraphNode).where(GraphNode.repository_id == repository_id)
            )

        # Deduplicate nodes by (node_type, name)
        node_map: dict[tuple[str, str], GraphNode] = {}
        created_nodes = 0

        for p_node in result.nodes:
            key = (p_node.node_type, p_node.name)
            if key in node_map:
                continue

            g_node = GraphNode(
                node_type=p_node.node_type,
                name=p_node.name,
                path=p_node.path,
                properties=p_node.properties,
                repository_id=repository_id,
            )
            db.add(g_node)
            node_map[key] = g_node
            created_nodes += 1

        await db.flush()

        # Build name -> node lookup for edge resolution
        # First check node_type + name, fallback to just name
        by_type_and_name: dict[tuple[str, str], GraphNode] = {
            (n.node_type, n.name): n for n in node_map.values()
        }
        by_name: dict[str, GraphNode] = {n.name: n for n in node_map.values()}

        created_edges = 0
        seen_edges: set[tuple[uuid.UUID, uuid.UUID, str]] = set()

        for p_edge in result.edges:
            src = by_type_and_name.get((p_edge.source_type, p_edge.source_name)) or by_name.get(p_edge.source_name)
            tgt = by_type_and_name.get((p_edge.target_type, p_edge.target_name)) or by_name.get(p_edge.target_name)

            if src and tgt and src.id != tgt.id:
                edge_sig = (src.id, tgt.id, p_edge.relationship_type)
                if edge_sig not in seen_edges:
                    seen_edges.add(edge_sig)
                    g_edge = GraphEdge(
                        source_node_id=src.id,
                        target_node_id=tgt.id,
                        relationship_type=p_edge.relationship_type,
                        properties=p_edge.properties,
                    )
                    db.add(g_edge)
                    created_edges += 1

        # Audit log
        activity = Activity(
            actor="reality_engine",
            action="graph_ingested",
            entity_type="graph",
            entity_name=repo_name,
            details=f"Ingested {created_nodes} nodes and {created_edges} edges for {repo_name}",
        )
        db.add(activity)

        await db.commit()

        return {
            "repository": repo_name,
            "nodes_count": created_nodes,
            "edges_count": created_edges,
            "warnings_count": len(result.warnings),
        }
