"""Missing documentation detector."""

from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class MissingDocumentationDetector(BaseDetector):
    """Detects services, critical APIs, and public infrastructure lacking documentation."""

    detector_type = "missing_documentation"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        service_nodes = [n for n in nodes if n.get("node_type") == "service"]
        documented_targets: set[str] = set()

        for e in edges:
            if e.get("relationship_type") == "documents":
                target = e.get("target_node_id")
                if target:
                    documented_targets.add(target)

        # Also check documentation nodes that mention service names
        doc_nodes = [n for n in nodes if n.get("node_type") == "documentation"]
        doc_texts = " ".join([d.get("properties", {}).get("content", "").lower() for d in doc_nodes])

        for s in service_nodes:
            s_id = s.get("id")
            s_name = s.get("name", "")

            # If service node has no 'documents' edge and its name is not mentioned in any doc node
            if s_id not in documented_targets and s_name.lower() not in doc_texts:
                results.append(
                    DiscrepancyResult(
                        title=f"Missing Service Documentation: '{s_name}'",
                        finding_type=self.detector_type,
                        severity="low",
                        confidence=0.85,
                        description=(
                            f"Service '{s_name}' is declared in the ecosystem but lacks architectural "
                            "documentation, runbooks, or API specifications."
                        ),
                        file_path=s.get("path"),
                        expected=f"Documentation or README entry for '{s_name}'",
                        actual="No associated documentation node or reference",
                        related_node_ids=[s_id] if s_id else [],
                        metadata={"service": s_name},
                    )
                )

        return results
