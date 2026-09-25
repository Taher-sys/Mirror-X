"""Context Engine Orchestrator."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context.detectors import ALL_DETECTORS, BaseDetector, DiscrepancyResult
from app.models.finding import Finding
from app.models.graph import GraphEdge, GraphNode


class ContextEngine:
    """Orchestrates discrepancy analysis across the Reality Graph and repository files."""

    def __init__(self, detectors: list[BaseDetector] | None = None):
        self.detectors = detectors or [d_cls() for d_cls in ALL_DETECTORS]

    async def analyze_graph_data(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
        db: AsyncSession | None = None,
        repository_id: uuid.UUID | None = None,
    ) -> list[DiscrepancyResult]:
        """Execute all detectors on provided graph data and optionally persist findings to DB."""
        all_results: list[DiscrepancyResult] = []

        for detector in self.detectors:
            results = detector.detect(nodes, edges, file_tree)
            all_results.extend(results)

        if db:
            await self._persist_findings(db, all_results, repository_id)

        return all_results

    async def analyze_repository(
        self,
        db: AsyncSession,
        repository_id: uuid.UUID | None = None,
        file_tree: dict[str, str] | None = None,
    ) -> list[Finding]:
        """Load graph nodes and edges from database, run all detectors, and persist findings."""
        # Query graph nodes
        stmt_nodes = select(GraphNode)
        stmt_edges = select(GraphEdge)
        if repository_id:
            stmt_nodes = stmt_nodes.where(
                (GraphNode.repository_id == repository_id) | (GraphNode.repository_id.is_(None))
            )

        res_nodes = await db.execute(stmt_nodes)
        nodes_db = res_nodes.scalars().all()

        res_edges = await db.execute(stmt_edges)
        edges_db = res_edges.scalars().all()

        # Format into dicts for detector processing
        nodes_payload = [
            {
                "id": str(n.id),
                "name": n.name,
                "node_type": n.node_type,
                "path": n.path,
                "properties": n.properties or {},
                "repository_id": str(n.repository_id) if n.repository_id else None,
            }
            for n in nodes_db
        ]

        edges_payload = [
            {
                "id": str(e.id),
                "source_node_id": str(e.source_node_id),
                "target_node_id": str(e.target_node_id),
                "relationship_type": e.relationship_type,
                "properties": e.properties or {},
            }
            for e in edges_db
        ]

        discrepancies = []
        for detector in self.detectors:
            discrepancies.extend(detector.detect(nodes_payload, edges_payload, file_tree))

        persisted_findings = await self._persist_findings(db, discrepancies, repository_id)
        return persisted_findings

    async def _persist_findings(
        self,
        db: AsyncSession,
        discrepancies: list[DiscrepancyResult],
        repository_id: uuid.UUID | None = None,
    ) -> list[Finding]:
        """Save discrepancy results to findings table avoiding duplicates."""
        persisted: list[Finding] = []

        # Fetch existing findings for this repository
        stmt = select(Finding)
        if repository_id:
            stmt = stmt.where(Finding.repository_id == repository_id)
        existing_res = await db.execute(stmt)
        existing_findings = {
            (f.title, f.finding_type): f for f in existing_res.scalars().all()
        }

        for d in discrepancies:
            key = (d.title, d.finding_type)
            if key in existing_findings:
                # Update existing finding evidence and status
                f = existing_findings[key]
                f.severity = d.severity
                f.confidence = d.confidence
                f.description = d.description
                f.evidence_payload = d.to_evidence_payload()
                if f.status == "resolved":
                    f.status = "open"  # Reopen if drift reoccurred
                persisted.append(f)
            else:
                new_finding = Finding(
                    title=d.title,
                    finding_type=d.finding_type,
                    severity=d.severity,
                    confidence=d.confidence,
                    description=d.description,
                    evidence_payload=d.to_evidence_payload(),
                    status="open",
                    repository_id=repository_id,
                )
                db.add(new_finding)
                persisted.append(new_finding)

        await db.flush()
        stmt_reload = select(Finding).order_by(Finding.created_at.desc())
        if repository_id:
            stmt_reload = stmt_reload.where(Finding.repository_id == repository_id)
        reload_res = await db.execute(stmt_reload)
        return list(reload_res.scalars().all())
