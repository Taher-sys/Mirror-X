"""Parser for requirements.txt files."""

from pathlib import Path

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_requirements_txt(content: str, file_path: str = "requirements.txt") -> IngestionResult:
    """Parse requirements.txt and extract Python components."""
    result = IngestionResult()
    service_name = Path(file_path).parent.name or "python-app"

    lines = content.splitlines()
    for line in lines:
        cleaned = line.strip()
        if not cleaned or cleaned.startswith(("#", "-")):
            continue

        # Extract package name and version specification
        pkg_name = cleaned.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
        if not pkg_name:
            continue

        comp_node = ParsedNode(
            name=pkg_name,
            node_type="component",
            path=file_path,
            properties={"declaration": cleaned},
        )
        result.nodes.append(comp_node)
        result.edges.append(
            ParsedEdge(
                source_name=service_name,
                source_type="service",
                target_name=pkg_name,
                target_type="component",
                relationship_type="depends_on",
                properties={"spec": cleaned},
            )
        )

    return result
