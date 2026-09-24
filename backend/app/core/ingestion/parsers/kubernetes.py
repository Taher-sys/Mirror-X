"""Parser for basic Kubernetes YAML manifests."""

import yaml

from app.core.ingestion.types import IngestionResult, ParsedEdge, ParsedNode


def parse_kubernetes(content: str, file_path: str = "deployment.yaml") -> IngestionResult:
    """Parse Kubernetes multi-document YAML and extract Deployments, Services, and workloads."""
    result = IngestionResult()

    try:
        docs = list(yaml.safe_load_all(content))
    except (yaml.YAMLError, ValueError, TypeError) as e:
        result.warnings.append(f"Failed to parse Kubernetes manifest {file_path}: {e}")
        return result


    for doc in docs:
        if not isinstance(doc, dict):
            continue

        kind = doc.get("kind", "")
        metadata = doc.get("metadata", {})
        name = metadata.get("name", "k8s-resource")
        namespace = metadata.get("namespace", "default")
        spec = doc.get("spec", {})

        if kind in ("Deployment", "StatefulSet", "DaemonSet"):
            template_spec = spec.get("template", {}).get("spec", {})
            containers = template_spec.get("containers", [])
            images = [c.get("image") for c in containers if c.get("image")]

            deploy_node = ParsedNode(
                name=f"{name}-k8s",
                node_type="deployment",
                path=file_path,
                properties={
                    "kind": kind,
                    "namespace": namespace,
                    "replicas": spec.get("replicas", 1),
                    "images": images,
                },
            )
            result.nodes.append(deploy_node)

            # Link matching service if containers declare service ports
            result.edges.append(
                ParsedEdge(
                    source_name=name,
                    source_type="service",
                    target_name=f"{name}-k8s",
                    target_type="deployment",
                    relationship_type="deployed_as",
                    properties={"namespace": namespace},
                )
            )

        elif kind == "Service":
            ports = spec.get("ports", [])
            selector = spec.get("selector", {})

            svc_node = ParsedNode(
                name=name,
                node_type="service",
                path=file_path,
                properties={
                    "kind": "K8s-Service",
                    "namespace": namespace,
                    "ports": ports,
                    "selector": selector,
                },
            )
            result.nodes.append(svc_node)

    return result
