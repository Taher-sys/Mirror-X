"""Parser for OpenAPI / Swagger specifications."""

import json
from typing import Any

import yaml

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_openapi(content: str, file_path: str = "openapi.yaml") -> IngestionResult:
    """Parse OpenAPI 3.x / Swagger spec and extract API endpoints and schema models."""
    result = IngestionResult()

    try:
        if content.strip().startswith("{"):
            data: dict[str, Any] = json.loads(content)
        else:
            data = yaml.safe_load(content) or {}
    except (yaml.YAMLError, json.JSONDecodeError, ValueError, TypeError) as e:
        result.warnings.append(f"Failed to parse OpenAPI {file_path}: {e}")
        return result

    info = data.get("info", {})
    service_name = info.get("title", "API Gateway").replace(" ", "-").lower()

    # Create service representing this API provider
    service_node = ParsedNode(
        name=service_name,
        node_type="service",
        path=file_path,
        properties={
            "version": info.get("version", "1.0.0"),
            "description": info.get("description", ""),
            "spec_format": "openapi",
        },
    )
    result.nodes.append(service_node)

    paths = data.get("paths", {})
    for path_url, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in ("get", "post", "put", "delete", "patch", "options", "head"):
            if method not in path_item:
                continue

            op = path_item[method]
            if not isinstance(op, dict):
                continue

            endpoint_name = f"{method.upper()} {path_url}"
            summary = op.get("summary") or op.get("operationId") or endpoint_name

            api_node = ParsedNode(
                name=endpoint_name,
                node_type="api",
                path=file_path,
                properties={
                    "method": method.upper(),
                    "path": path_url,
                    "summary": summary,
                    "operation_id": op.get("operationId"),
                    "tags": op.get("tags", []),
                    "deprecated": op.get("deprecated", False),
                },
            )
            result.nodes.append(api_node)

            # Relationship: service contains api
            result.edges.append(
                ParsedEdge(
                    source_name=service_name,
                    source_type="service",
                    target_name=endpoint_name,
                    target_type="api",
                    relationship_type="contains",
                    properties={"method": method.upper()},
                )
            )

    return result
