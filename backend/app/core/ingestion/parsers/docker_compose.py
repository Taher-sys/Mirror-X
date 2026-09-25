"""Parser for docker-compose.yml files."""

from typing import Any

import yaml

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode

DATABASE_IMAGES = ("mysql", "postgres", "postgresql", "redis", "mongo", "mongodb", "mariadb", "cockroach")


def parse_docker_compose(content: str, file_path: str = "docker-compose.yml") -> IngestionResult:
    """Parse docker-compose and extract services, databases, deployments, and dependency edges."""
    result = IngestionResult()

    try:
        data: dict[str, Any] = yaml.safe_load(content) or {}
    except (yaml.YAMLError, ValueError, TypeError) as e:
        result.warnings.append(f"Failed to parse {file_path}: {e}")
        return result

    services = data.get("services", {})
    for svc_name, svc_conf in services.items():
        if not isinstance(svc_conf, dict):
            continue

        image = str(svc_conf.get("image", ""))
        ports = svc_conf.get("ports", [])
        depends_on = svc_conf.get("depends_on", [])
        if isinstance(depends_on, dict):
            depends_on = list(depends_on.keys())

        # Categorize as database or application service
        is_database = any(db_kw in image.lower() or db_kw in svc_name.lower() for db_kw in DATABASE_IMAGES)

        if is_database:
            db_node = ParsedNode(
                name=svc_name,
                node_type="database",
                path=file_path,
                properties={
                    "image": image,
                    "ports": ports,
                    "engine": image.split(":")[0] if image else "rdbms",
                },
            )
            result.nodes.append(db_node)
        else:
            service_node = ParsedNode(
                name=svc_name,
                node_type="service",
                path=file_path,
                properties={
                    "image": image,
                    "ports": ports,
                    "environment_keys": list(svc_conf.get("environment", {}).keys())
                    if isinstance(svc_conf.get("environment"), dict)
                    else [],
                },
            )
            result.nodes.append(service_node)

        # Deployment representation
        deploy_node = ParsedNode(
            name=f"{svc_name}-compose-deployment",
            node_type="deployment",
            path=file_path,
            properties={"service": svc_name, "ports": ports, "kind": "docker-compose"},
        )
        result.nodes.append(deploy_node)

        result.edges.append(
            ParsedEdge(
                source_name=svc_name,
                source_type="database" if is_database else "service",
                target_name=f"{svc_name}-compose-deployment",
                target_type="deployment",
                relationship_type="deployed_as",
            )
        )

        # depends_on relationships
        for dep in depends_on:
            result.edges.append(
                ParsedEdge(
                    source_name=svc_name,
                    source_type="service",
                    target_name=dep,
                    target_type="database" if any(db_kw in dep.lower() for db_kw in DATABASE_IMAGES) else "service",
                    relationship_type="depends_on",
                )
            )

    return result
