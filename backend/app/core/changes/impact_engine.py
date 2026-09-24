"""Impact Calculation Engine for Phase 5 Change Twin."""

import re
from dataclasses import dataclass, field
from typing import Any

from app.core.changes.diff_parser import FileDiff, GitDiffParser


@dataclass
class ImpactedNode:
    """A node in the Reality Graph impacted by a proposed change."""

    node_id: str
    name: str
    node_type: str
    path: str | None
    impact_type: str  # 'direct' or 'indirect'
    depth: int  # 0 for direct, 1+ for indirect
    propagation_path: list[str] = field(default_factory=list)  # e.g. ["orders", "calls", "payment-service"]
    reason: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class BreakingChangeWarning:
    """Specific breaking change risk identified during impact analysis."""

    title: str
    severity: str  # 'critical', 'high', 'medium'
    source_node: str
    impacted_nodes: list[str]
    description: str


@dataclass
class ImpactAnalysisResult:
    """Full impact assessment for a proposed change."""

    direct_nodes: list[ImpactedNode]
    indirect_nodes: list[ImpactedNode]
    affected_categories: dict[str, int]
    breaking_changes: list[BreakingChangeWarning]
    risk_score: float
    risk_level: str  # 'critical', 'high', 'medium', 'low'
    file_diffs: list[FileDiff]

    def to_dict(self) -> dict[str, Any]:
        return {
            "direct_impact_count": len(self.direct_nodes),
            "indirect_impact_count": len(self.indirect_nodes),
            "total_impacted_nodes": len(self.direct_nodes) + len(self.indirect_nodes),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "affected_categories": self.affected_categories,
            "breaking_changes": [
                {
                    "title": b.title,
                    "severity": b.severity,
                    "source_node": b.source_node,
                    "impacted_nodes": b.impacted_nodes,
                    "description": b.description,
                }
                for b in self.breaking_changes
            ],
            "direct_nodes": [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "path": n.path,
                    "reason": n.reason,
                    "properties": n.properties,
                }
                for n in self.direct_nodes
            ],
            "indirect_nodes": [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "path": n.path,
                    "depth": n.depth,
                    "propagation_path": n.propagation_path,
                    "reason": n.reason,
                    "properties": n.properties,
                }
                for n in self.indirect_nodes
            ],
            "modified_files": [
                {
                    "file_path": f.file_path,
                    "change_type": f.change_type,
                    "additions": len(f.added_lines),
                    "deletions": len(f.deleted_lines),
                }
                for f in self.file_diffs
            ],
        }


class ChangeImpactEngine:
    """Calculates direct and indirect blast radius of code changes across the Reality Graph."""

    def analyze(
        self,
        diff_text: str,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> ImpactAnalysisResult:
        file_diffs = GitDiffParser.parse(diff_text)
        changed_paths = {f.file_path.replace("\\", "/"): f for f in file_diffs}

        node_map = {str(n["id"]): n for n in nodes if n.get("id")}

        # Build adjacency maps for relationships
        # Outgoing edges: source -> [edge]
        outgoing: dict[str, list[dict[str, Any]]] = {}
        # Incoming edges: target -> [edge]
        incoming: dict[str, list[dict[str, Any]]] = {}

        for e in edges:
            src = str(e.get("source_node_id"))
            tgt = str(e.get("target_node_id"))
            outgoing.setdefault(src, []).append(e)
            incoming.setdefault(tgt, []).append(e)

        # 1. Identify Direct Impact Nodes
        direct_nodes: list[ImpactedNode] = []
        direct_ids: set[str] = set()

        for node in nodes:
            nid = str(node["id"])
            npath = (node.get("path") or "").replace("\\", "/")
            nname = node.get("name", "")
            matched_diff = None

            # Path match
            if npath in changed_paths:
                matched_diff = changed_paths[npath]
            else:
                for cpath, fdiff in changed_paths.items():
                    if npath and (cpath.startswith(npath) or npath.startswith(cpath) or cpath.endswith(npath)):
                        matched_diff = fdiff
                        break
                    # Route path match for API nodes
                    if node.get("node_type") == "api" and nname in fdiff.deleted_lines:
                        matched_diff = fdiff
                        break

            if matched_diff and nid not in direct_ids:
                direct_ids.add(nid)
                direct_nodes.append(
                    ImpactedNode(
                        node_id=nid,
                        name=nname,
                        node_type=node.get("node_type", "component"),
                        path=npath,
                        impact_type="direct",
                        depth=0,
                        reason=f"File '{matched_diff.file_path}' {matched_diff.change_type} in change payload",
                        properties=node.get("properties", {}) or {},
                    )
                )

        # 2. Identify Indirect Impact Nodes via Graph Traversal (BFS)
        indirect_nodes: list[ImpactedNode] = []
        visited_ids: set[str] = set(direct_ids)
        queue: list[tuple[str, int, list[str]]] = [(nid, 0, [node_map[nid]["name"]]) for nid in direct_ids]

        while queue:
            curr_id, curr_depth, curr_path = queue.pop(0)
            curr_node = node_map.get(curr_id)
            if not curr_node:
                continue

            # Traverse upstream dependents (nodes that call, depend_on, read_from, write_to this node)
            for edge in incoming.get(curr_id, []):
                dep_id = str(edge.get("source_node_id"))
                rel = edge.get("relationship_type", "relies_on")
                if dep_id not in visited_ids and dep_id in node_map:
                    visited_ids.add(dep_id)
                    dep_node = node_map[dep_id]
                    step_path = [*curr_path, f"({rel})", dep_node["name"]]
                    queue.append((dep_id, curr_depth + 1, step_path))

                    indirect_nodes.append(
                        ImpactedNode(
                            node_id=dep_id,
                            name=dep_node["name"],
                            node_type=dep_node.get("node_type", "component"),
                            path=dep_node.get("path"),
                            impact_type="indirect",
                            depth=curr_depth + 1,
                            propagation_path=step_path,
                            reason=f"Upstream consumer: {dep_node['name']} {rel} {curr_node['name']}",
                            properties=dep_node.get("properties", {}) or {},
                        )
                    )

            # Traverse downstream deployed/documented dependents
            for edge in outgoing.get(curr_id, []):
                target_id = str(edge.get("target_node_id"))
                rel = edge.get("relationship_type", "")
                if rel in ("deployed_as", "documents") and target_id not in visited_ids and target_id in node_map:
                    visited_ids.add(target_id)
                    target_node = node_map[target_id]
                    step_path = [*curr_path, f"({rel})", target_node["name"]]
                    queue.append((target_id, curr_depth + 1, step_path))

                    indirect_nodes.append(
                        ImpactedNode(
                            node_id=target_id,
                            name=target_node["name"],
                            node_type=target_node.get("node_type", "component"),
                            path=target_node.get("path"),
                            impact_type="indirect",
                            depth=curr_depth + 1,
                            propagation_path=step_path,
                            reason=f"Downstream association: {curr_node['name']} {rel} {target_node['name']}",
                            properties=target_node.get("properties", {}) or {},
                        )
                    )

        # 3. Detect Breaking Changes & Compute Risk
        breaking_changes: list[BreakingChangeWarning] = []
        base_risk = 0.0

        for d_node in direct_nodes:
            # Score direct impact by node criticality
            ntype = d_node.node_type
            if ntype in ("database", "table"):
                base_risk += 25.0
            elif ntype == "service":
                base_risk += 20.0
            elif ntype == "api" or ntype == "infrastructure":
                base_risk += 15.0
            else:
                base_risk += 5.0

            # Check if any deleted lines correspond to removed API or table schema
            for fdiff in file_diffs:
                if fdiff.change_type == "deleted":
                    breaking_changes.append(
                        BreakingChangeWarning(
                            title=f"Entity Deletion: {fdiff.file_path}",
                            severity="critical",
                            source_node=d_node.name,
                            impacted_nodes=[n.name for n in indirect_nodes],
                            description=f"File '{fdiff.file_path}' was completely deleted, breaking downstream dependents.",
                        )
                    )
                    base_risk += 35.0
                elif any(re.search(r"DROP\s+COLUMN|ALTER\s+TABLE.*DROP", line, re.IGNORECASE) for line in fdiff.deleted_lines):
                    breaking_changes.append(
                        BreakingChangeWarning(
                            title=f"Database Column Dropped in {d_node.name}",
                            severity="critical",
                            source_node=d_node.name,
                            impacted_nodes=[n.name for n in indirect_nodes if n.node_type == "service"],
                            description="Schema migration drops or alters existing columns, which may break active ORM queries.",
                        )
                    )
                    base_risk += 30.0

            # If an API or Service has many indirect dependents, flag high blast radius
            downstream_callers = [
                n.name for n in indirect_nodes if n.propagation_path and "(calls)" in n.propagation_path or "(depends_on)" in n.propagation_path
            ]
            if len(downstream_callers) >= 2:
                breaking_changes.append(
                    BreakingChangeWarning(
                        title=f"High Blast Radius on {d_node.name}",
                        severity="high",
                        source_node=d_node.name,
                        impacted_nodes=downstream_callers,
                        description=(
                            f"Modifying '{d_node.name}' propagates to {len(downstream_callers)} downstream services: "
                            f"{', '.join(downstream_callers[:4])}."
                        ),
                    )
                )

        # Indirect impact adds 8 points per affected node
        base_risk += len(indirect_nodes) * 8.0

        risk_score = min(100.0, round(base_risk, 1))
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 15:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Tally categories
        affected_categories: dict[str, int] = {}
        for n in [*direct_nodes, *indirect_nodes]:
            affected_categories[n.node_type] = affected_categories.get(n.node_type, 0) + 1

        return ImpactAnalysisResult(
            direct_nodes=direct_nodes,
            indirect_nodes=indirect_nodes,
            affected_categories=affected_categories,
            breaking_changes=breaking_changes,
            risk_score=risk_score,
            risk_level=risk_level,
            file_diffs=file_diffs,
        )
