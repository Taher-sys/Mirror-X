"""Documentation drift detector."""

import re
from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class DocumentationDriftDetector(BaseDetector):
    """Detects outdated references to deprecated or nonexistent services, endpoints, and configs in docs."""

    detector_type = "documentation_drift"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        # Collect active names of entities
        service_names = {n.get("name", "").lower() for n in nodes if n.get("node_type") == "service"}
        api_paths = {n.get("name", "") for n in nodes if n.get("node_type") == "api"}
        for n in nodes:
            if n.get("node_type") == "api" and n.get("properties", {}).get("path"):
                api_paths.add(n["properties"]["path"])

        doc_nodes = [n for n in nodes if n.get("node_type") == "documentation"]

        # Examine markdown files or doc nodes
        docs_to_check: list[tuple[str, str]] = []
        for d in doc_nodes:
            path = d.get("path") or d.get("name", "")
            content = d.get("properties", {}).get("content", "")
            if content:
                docs_to_check.append((path, content))

        if file_tree:
            for fpath, content in file_tree.items():
                if fpath.endswith((".md", ".rst", ".txt")) and not any(fpath == p for p, _ in docs_to_check):
                    docs_to_check.append((fpath, content))

        for doc_path, content in docs_to_check:
            lines = content.splitlines()

            # Check 1: Explicitly documented endpoints like `GET /api/v1/...` or `POST /...`
            endpoint_matches = re.finditer(
                r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[a-zA-Z0-9_\-/{}:]+)", content
            )
            for m in endpoint_matches:
                verb = m.group(1)
                route = m.group(2)
                # Ignore generic root or wildcards
                if route in ["/", "/health", "/docs", "/openapi.json"]:
                    continue

                # Check if route exists in reality graph
                norm_route = re.sub(r"\{[^}]+\}|:[a-zA-Z0-9_]+|<[^>]+>", "{param}", route)
                matched = False
                for active_p in api_paths:
                    norm_active = re.sub(r"\{[^}]+\}|:[a-zA-Z0-9_]+|<[^>]+>", "{param}", active_p)
                    if norm_route == norm_active:
                        matched = True
                        break

                if not matched and api_paths:
                    line_no = content[: m.start()].count("\n") + 1
                    snippet = lines[line_no - 1] if line_no <= len(lines) else ""
                    results.append(
                        DiscrepancyResult(
                            title=f"Documentation Drift: Deprecated Endpoint '{verb} {route}' in {doc_path}",
                            finding_type=self.detector_type,
                            severity="medium",
                            confidence=0.87,
                            description=(
                                f"Document '{doc_path}' references endpoint '{verb} {route}', which does not exist "
                                "in the Reality Graph or active API schema contracts."
                            ),
                            file_path=doc_path,
                            line_number=line_no,
                            code_snippet=snippet.strip(),
                            expected="Active endpoint matching OpenAPI specification",
                            actual=f"{verb} {route}",
                            metadata={"doc": doc_path, "referenced_endpoint": route},
                        )
                    )

            # Check 2: References to legacy services (e.g. `*-v1`, `legacy-*`, `deprecated-*`)
            legacy_refs = re.finditer(
                r"\b([a-zA-Z0-9_\-]+(?:-service|-worker|-api|-v1|-legacy))\b", content, re.IGNORECASE
            )
            for m in legacy_refs:
                ref_name = m.group(1).lower()
                if service_names and ref_name not in service_names and ("legacy" in ref_name or "deprecated" in ref_name or "-v1" in ref_name):
                    line_no = content[: m.start()].count("\n") + 1
                    snippet = lines[line_no - 1] if line_no <= len(lines) else ""
                    results.append(
                        DiscrepancyResult(
                            title=f"Documentation Drift: Stale Service Reference '{ref_name}'",
                            finding_type=self.detector_type,
                            severity="low",
                            confidence=0.82,
                            description=(
                                f"Document '{doc_path}' references retired or non-existent service '{ref_name}'."
                            ),
                            file_path=doc_path,
                            line_number=line_no,
                            code_snippet=snippet.strip(),
                            expected=f"Active service from {sorted(list(service_names)[:5])}",
                            actual=ref_name,
                        )
                    )

        return results
