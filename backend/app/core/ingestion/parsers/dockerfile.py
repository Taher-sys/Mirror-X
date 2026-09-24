"""Parser for Dockerfile."""

import re
from pathlib import Path

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_dockerfile(content: str, file_path: str = "Dockerfile") -> IngestionResult:
    """Parse Dockerfile and extract deployment and exposed container attributes."""
    result = IngestionResult()
    service_name = Path(file_path).parent.name or "container-service"
    deploy_name = f"{service_name}-container"

    base_images = re.findall(r"^FROM\s+([^\s\n]+)", content, re.MULTILINE | re.IGNORECASE)
    exposed_ports = re.findall(r"^EXPOSE\s+([^\s\n]+)", content, re.MULTILINE | re.IGNORECASE)
    entrypoints = re.findall(r"^ENTRYPOINT\s+(.+)", content, re.MULTILINE | re.IGNORECASE)
    cmds = re.findall(r"^CMD\s+(.+)", content, re.MULTILINE | re.IGNORECASE)

    deployment_node = ParsedNode(
        name=deploy_name,
        node_type="deployment",
        path=file_path,
        properties={
            "base_image": base_images[-1] if base_images else "scratch",
            "exposed_ports": exposed_ports,
            "entrypoint": entrypoints[-1] if entrypoints else None,
            "cmd": cmds[-1] if cmds else None,
            "kind": "Docker",
        },
    )
    result.nodes.append(deployment_node)

    # Relationship: service deployed_as deployment
    result.edges.append(
        ParsedEdge(
            source_name=service_name,
            source_type="service",
            target_name=deploy_name,
            target_type="deployment",
            relationship_type="deployed_as",
            properties={"ports": exposed_ports},
        )
    )

    return result
