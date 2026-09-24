"""Parser for package.json files."""

import json
from pathlib import Path
from typing import Any

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_package_json(content: str, file_path: str = "package.json") -> IngestionResult:
    """Parse package.json and extract service, components, and dependency relationships."""
    result = IngestionResult()

    try:
        data: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as e:
        result.warnings.append(f"Failed to parse {file_path}: {e}")
        return result

    name = data.get("name") or Path(file_path).parent.name or "node-service"
    version = data.get("version", "0.0.0")
    scripts = data.get("scripts", {})

    service_node = ParsedNode(
        name=name,
        node_type="service",
        path=file_path,
        properties={
            "version": version,
            "runtime": f"Node.js ({data.get('engines', {}).get('node', '>=18')})",
            "scripts": list(scripts.keys()),
            "type": "frontend" if "next" in data.get("dependencies", {}) or "react" in data.get("dependencies", {}) else "api",
        },
    )
    result.nodes.append(service_node)

    # Extract production dependencies
    dependencies = data.get("dependencies", {})
    for dep_name, dep_version in dependencies.items():
        comp_node = ParsedNode(
            name=dep_name,
            node_type="component",
            path=file_path,
            properties={"version": dep_version, "dependency_type": "production"},
        )
        result.nodes.append(comp_node)
        result.edges.append(
            ParsedEdge(
                source_name=name,
                source_type="service",
                target_name=dep_name,
                target_type="component",
                relationship_type="depends_on",
                properties={"version_constraint": dep_version},
            )
        )

    return result
