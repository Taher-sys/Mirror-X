"""Parser for pyproject.toml files."""

import tomllib
from pathlib import Path
from typing import Any

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_pyproject_toml(content: str, file_path: str = "pyproject.toml") -> IngestionResult:
    """Parse pyproject.toml and extract python service and dependencies."""
    result = IngestionResult()

    try:
        data: dict[str, Any] = tomllib.loads(content)
    except (tomllib.TOMLDecodeError, ValueError, TypeError) as e:
        result.warnings.append(f"Failed to parse {file_path}: {e}")
        return result

    # Check project table or tool.poetry
    project_data = data.get("project", {})
    poetry_data = data.get("tool", {}).get("poetry", {})

    name = project_data.get("name") or poetry_data.get("name") or Path(file_path).parent.name or "python-service"
    version = project_data.get("version") or poetry_data.get("version", "0.1.0")

    service_node = ParsedNode(
        name=name,
        node_type="service",
        path=file_path,
        properties={
            "version": version,
            "runtime": f"Python ({project_data.get('requires-python', '>=3.11')})",
            "type": "api",
        },
    )
    result.nodes.append(service_node)

    # Dependencies from project.dependencies or poetry.dependencies
    deps: list[str] = project_data.get("dependencies", [])
    if not deps and "dependencies" in poetry_data:
        deps = [f"{k}{v}" for k, v in poetry_data["dependencies"].items() if k != "python"]

    for dep_entry in deps:
        # Normalize package name (e.g. "fastapi>=0.115.0" -> "fastapi")
        pkg_name = dep_entry.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
        if not pkg_name:
            continue

        comp_node = ParsedNode(
            name=pkg_name,
            node_type="component",
            path=file_path,
            properties={"raw_declaration": dep_entry},
        )
        result.nodes.append(comp_node)
        result.edges.append(
            ParsedEdge(
                source_name=name,
                source_type="service",
                target_name=pkg_name,
                target_type="component",
                relationship_type="depends_on",
                properties={"raw": dep_entry},
            )
        )

    return result
