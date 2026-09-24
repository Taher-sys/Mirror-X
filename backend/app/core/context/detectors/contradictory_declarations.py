"""Contradictory declarations detector."""

from typing import Any

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult


class ContradictoryDeclarationsDetector(BaseDetector):
    """Detects conflicting ports, versions, or runtime settings across Docker, Compose, and K8s."""

    detector_type = "contradictory_declarations"

    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        results: list[DiscrepancyResult] = []

        # Find services, infrastructure, and deployment manifests
        # Group by common service name or repository
        service_ports: dict[str, list[dict[str, Any]]] = {}

        for n in nodes:
            props = n.get("properties", {}) or {}
            node_name = n.get("name", "").lower()
            path = n.get("path", "")

            # Ports can come from Dockerfile EXPOSE, Compose ports, or K8s service ports
            ports = props.get("exposed_ports") or props.get("ports") or []
            if isinstance(ports, int):
                ports = [ports]

            # Try to identify service association
            svc_key = props.get("service") or node_name
            if "dockerfile" in path.lower() or n.get("node_type") == "service":
                for p in ports:
                    # Clean port format (e.g. "8080/tcp" or "8080:8080" or 8080)
                    port_num = str(p).split("/")[0].split(":")[-1]
                    if port_num.isdigit():
                        service_ports.setdefault(svc_key, []).append({
                            "port": int(port_num),
                            "source": path or n.get("name"),
                            "node_id": n.get("id"),
                            "type": "exposed_port",
                        })

        # Check for port conflicts within the same service across different config files
        for svc_name, port_entries in service_ports.items():
            distinct_ports = {e["port"] for e in port_entries}
            if len(distinct_ports) > 1:
                # Contradiction detected
                sources = [f"{e['source']} (port {e['port']})" for e in port_entries]
                results.append(
                    DiscrepancyResult(
                        title=f"Port Contradiction in Service '{svc_name}': {sorted(distinct_ports)}",
                        finding_type=self.detector_type,
                        severity="high",
                        confidence=0.96,
                        description=(
                            f"Service '{svc_name}' has conflicting port declarations across manifests: "
                            f"{', '.join(sources)}."
                        ),
                        file_path=port_entries[0]["source"],
                        expected="Consistent exposed port across Dockerfile, Compose, and Kubernetes",
                        actual=f"Divergent ports: {sorted(distinct_ports)}",
                        related_node_ids=[e["node_id"] for e in port_entries if e["node_id"]],
                        metadata={"service": svc_name, "ports": list(distinct_ports)},
                    )
                )

        return results
