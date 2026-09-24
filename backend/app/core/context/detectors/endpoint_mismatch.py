"""Endpoint mismatch detector."""

import re
from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class EndpointMismatchDetector(BaseDetector):
    """Detects discrepancies between code/router implementations and OpenAPI/API specs."""

    detector_type = "endpoint_mismatch"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        # 1. Compare API nodes declared in spec vs defined in code
        api_nodes = [n for n in nodes if n.get("node_type") == "api"]

        spec_endpoints: dict[str, dict[str, Any]] = {}
        code_endpoints: dict[str, dict[str, Any]] = {}

        for n in api_nodes:
            props = n.get("properties", {}) or {}
            source = props.get("source", "spec" if "summary" in props or "operation_id" in props else "code")
            path = props.get("path") or n.get("name")
            methods = {m.upper() for m in props.get("methods", ["GET"])}

            # Normalize path (e.g. {id} vs :id vs <id>)
            norm_path = re.sub(r"\{[^}]+\}|:[a-zA-Z0-9_]+|<[^>]+>", "{param}", path)

            entry = {
                "node_id": n.get("id"),
                "node_name": n.get("name"),
                "original_path": path,
                "methods": methods,
                "props": props,
                "path": n.get("path"),
            }

            if source == "spec":
                spec_endpoints[norm_path] = entry
            else:
                code_endpoints[norm_path] = entry

        # Check for code endpoints missing in spec
        for norm_path, c_info in code_endpoints.items():
            if norm_path not in spec_endpoints:
                results.append(
                    DiscrepancyResult(
                        title=f"Undocumented API Endpoint in Code: {c_info['original_path']}",
                        finding_type=self.detector_type,
                        severity="medium",
                        confidence=0.92,
                        description=(
                            f"Endpoint '{c_info['original_path']}' with methods {sorted(c_info['methods'])} "
                            "is implemented in router code but omitted from OpenAPI specifications."
                        ),
                        file_path=c_info.get("path"),
                        expected="Documented in openapi.json/yaml",
                        actual=f"{sorted(c_info['methods'])} {c_info['original_path']}",
                        related_node_ids=[c_info["node_id"]] if c_info["node_id"] else [],
                        metadata={"type": "missing_in_spec"},
                    )
                )
            else:
                s_info = spec_endpoints[norm_path]
                # Method mismatch
                diff_methods = c_info["methods"] - s_info["methods"]
                if diff_methods:
                    results.append(
                        DiscrepancyResult(
                            title=f"HTTP Method Mismatch on {c_info['original_path']}",
                            finding_type=self.detector_type,
                            severity="high",
                            confidence=0.95,
                            description=(
                                f"Endpoint '{c_info['original_path']}' implements {sorted(diff_methods)} in code, "
                                f"but the OpenAPI specification only defines {sorted(s_info['methods'])}."
                            ),
                            file_path=c_info.get("path"),
                            expected=sorted(s_info["methods"]),
                            actual=sorted(c_info["methods"]),
                            related_node_ids=[
                                nid for nid in [c_info["node_id"], s_info["node_id"]] if nid
                            ],
                            metadata={"type": "method_mismatch"},
                        )
                    )

        # Check for spec endpoints missing in code
        for norm_path, s_info in spec_endpoints.items():
            if norm_path not in code_endpoints:
                results.append(
                    DiscrepancyResult(
                        title=f"Unimplemented Contract Endpoint: {s_info['original_path']}",
                        finding_type=self.detector_type,
                        severity="high",
                        confidence=0.88,
                        description=(
                            f"OpenAPI spec defines endpoint '{s_info['original_path']}', "
                            "but no matching route handler was detected in service code."
                        ),
                        file_path=s_info.get("path"),
                        expected="Implementation in router or controller",
                        actual="No matching route handler found",
                        related_node_ids=[s_info["node_id"]] if s_info["node_id"] else [],
                        metadata={"type": "missing_in_code"},
                    )
                )

        # 2. Direct code inspection if file_tree is provided
        if file_tree:
            for fpath, content in file_tree.items():
                if fpath.endswith((".py", ".ts", ".js")):
                    for match in re.finditer(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content):
                        method = match.group(1).upper()
                        route = match.group(2)
                        norm_r = re.sub(r"\{[^}]+\}|:[a-zA-Z0-9_]+|<[^>]+>", "{param}", route)
                        if spec_endpoints and norm_r not in spec_endpoints:
                            line_no = content[: match.start()].count("\n") + 1
                            snippet = content.splitlines()[line_no - 1] if line_no <= len(content.splitlines()) else ""
                            results.append(
                                DiscrepancyResult(
                                    title=f"Unregistered Route: {method} {route}",
                                    finding_type=self.detector_type,
                                    severity="medium",
                                    confidence=0.90,
                                    description=f"Route '{method} {route}' in {fpath} is not declared in OpenAPI contract.",
                                    file_path=fpath,
                                    line_number=line_no,
                                    code_snippet=snippet.strip(),
                                    expected="Specification in openapi.yaml",
                                    actual=f"{method} {route}",
                                )
                            )

        return results
