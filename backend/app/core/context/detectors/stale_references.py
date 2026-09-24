"""Stale references detector."""

from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class StaleReferencesDetector(BaseDetector):
    """Detects dangling references in configurations, compose files, and code to deleted/missing entities."""

    detector_type = "stale_references"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        all_node_names = {n.get("name", "").lower() for n in nodes}
        node_id_map = {n.get("id"): n for n in nodes if n.get("id")}

        # Check declared dependencies inside properties of infrastructure and service nodes
        for n in nodes:
            props = n.get("properties", {}) or {}
            deps = props.get("dependencies") or props.get("depends_on") or []
            if isinstance(deps, list):
                for dep in deps:
                    dep_name = dep if isinstance(dep, str) else dep.get("name", "")
                    if not dep_name:
                        continue
                    # Ignore language package dependencies if node is a package.json
                    if n.get("path", "").endswith(("package.json", "pyproject.toml", "requirements.txt")):
                        continue

                    # For service / docker compose dependencies, verify target exists
                    if dep_name.lower() not in all_node_names:
                        results.append(
                            DiscrepancyResult(
                                title=f"Stale Dependency Reference: '{dep_name}' in '{n.get('name')}'",
                                finding_type=self.detector_type,
                                severity="high",
                                confidence=0.94,
                                description=(
                                    f"Configuration for '{n.get('name')}' declares a dependency on '{dep_name}', "
                                    "which cannot be resolved to any active service, database, or infrastructure component."
                                ),
                                file_path=n.get("path"),
                                expected=f"Active ecosystem entity '{dep_name}'",
                                actual="Unresolved dangling reference",
                                related_node_ids=[n.get("id")] if n.get("id") else [],
                                metadata={"caller": n.get("name"), "missing_target": dep_name},
                            )
                        )

        # Check graph edges where target node does not exist or target is marked inactive
        for e in edges:
            target_id = e.get("target_node_id")
            if target_id and target_id not in node_id_map:
                source = node_id_map.get(e.get("source_node_id"))
                results.append(
                    DiscrepancyResult(
                        title="Dangling Relationship Edge in Reality Graph",
                        finding_type=self.detector_type,
                        severity="medium",
                        confidence=0.99,
                        description=(
                            f"Graph edge '{e.get('relationship_type')}' from '{source.get('name') if source else 'Unknown'}' "
                            f"points to non-existent target node ID '{target_id}'."
                        ),
                        expected="Valid graph node ID",
                        actual=f"Dangling node ID {target_id}",
                        related_node_ids=[e.get("source_node_id")] if e.get("source_node_id") else [],
                    )
                )

        return results
