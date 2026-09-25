"""Parser for basic Terraform (.tf) infrastructure declarations."""

import re

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_terraform(content: str, file_path: str = "main.tf") -> IngestionResult:
    """Parse Terraform files and extract cloud resources, databases, and deployments."""
    result = IngestionResult()

    # Pattern: resource "<type>" "<name>" { ... }
    resource_pattern = re.compile(
        r'resource\s+"([a-zA-Z0-9_\-]+)"\s+"([a-zA-Z0-9_\-]+)"\s*\{(.*?)\}',
        re.DOTALL,
    )

    for match in resource_pattern.finditer(content):
        res_type = match.group(1)
        res_name = match.group(2)
        body = match.group(3)

        full_name = f"{res_type}.{res_name}"

        # Determine node type
        if any(
            db_kw in res_type.lower() for db_kw in ("db", "database", "rds", "postgres", "mysql", "dynamo", "redis")
        ):
            node_type = "database"
        else:
            node_type = "deployment"

        node = ParsedNode(
            name=full_name,
            node_type=node_type,
            path=file_path,
            properties={"resource_type": res_type, "identifier": res_name},
        )
        result.nodes.append(node)

        # Extract depends_on: depends_on = [ ... ]
        dep_match = re.search(r"depends_on\s*=\s*\[(.*?)\]", body, re.DOTALL)
        if dep_match:
            deps = [d.strip().replace('"', "") for d in dep_match.group(1).split(",") if d.strip()]
            for dep in deps:
                result.edges.append(
                    ParsedEdge(
                        source_name=full_name,
                        source_type=node_type,
                        target_name=dep,
                        target_type="deployment",
                        relationship_type="depends_on",
                    )
                )

    # Modules: module "<name>" { source = "..." }
    module_pattern = re.compile(r'module\s+"([a-zA-Z0-9_\-]+)"\s*\{(.*?)\}', re.DOTALL)
    for match in module_pattern.finditer(content):
        mod_name = match.group(1)
        mod_node = ParsedNode(
            name=f"module.{mod_name}",
            node_type="component",
            path=file_path,
            properties={"kind": "terraform_module"},
        )
        result.nodes.append(mod_node)

    return result
