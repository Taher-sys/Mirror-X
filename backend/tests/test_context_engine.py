"""Tests for Phase 4 Context Engine discrepancy detectors and APIs."""

import pytest
from httpx import AsyncClient

from app.core.context.detectors.contradictory_declarations import (
    ContradictoryDeclarationsDetector,
)
from app.core.context.detectors.documentation_drift import DocumentationDriftDetector
from app.core.context.detectors.endpoint_mismatch import EndpointMismatchDetector
from app.core.context.detectors.missing_documentation import (
    MissingDocumentationDetector,
)
from app.core.context.detectors.naming_mismatch import NamingMismatchDetector
from app.core.context.detectors.schema_mismatch import SchemaMismatchDetector
from app.core.context.detectors.stale_references import StaleReferencesDetector
from app.models.graph import GraphNode


def test_endpoint_mismatch_detector():
    detector = EndpointMismatchDetector()

    nodes = [
        # Spec defines GET /api/v1/orders
        {
            "id": "spec-1",
            "name": "/api/v1/orders",
            "node_type": "api",
            "path": "openapi.yaml",
            "properties": {
                "source": "spec",
                "methods": ["GET"],
                "summary": "List orders",
            },
        },
        # Code defines POST and GET on /api/v1/orders (method mismatch: POST not in spec)
        {
            "id": "code-1",
            "name": "/api/v1/orders",
            "node_type": "api",
            "path": "app/api/orders.py",
            "properties": {
                "source": "code",
                "methods": ["GET", "POST"],
            },
        },
        # Spec defines DELETE /api/v1/orders/{id} but code never implemented it
        {
            "id": "spec-2",
            "name": "/api/v1/orders/{id}",
            "node_type": "api",
            "path": "openapi.yaml",
            "properties": {
                "source": "spec",
                "methods": ["DELETE"],
                "summary": "Cancel order",
            },
        },
    ]

    results = detector.detect(nodes, [])
    types = [r.finding_type for r in results]
    assert all(t == "endpoint_mismatch" for t in types)

    titles = [r.title for r in results]
    # Check method mismatch detected
    assert any("HTTP Method Mismatch" in t for t in titles)
    # Check unimplemented endpoint detected
    assert any("Unimplemented Contract Endpoint" in t for t in titles)


def test_naming_mismatch_detector():
    detector = NamingMismatchDetector()

    nodes = [
        {
            "id": "tbl-1",
            "name": "customer_accounts",
            "node_type": "table",
            "path": "schema.sql",
            "properties": {
                "columns": [
                    {"name": "customer_id", "type": "INT"},
                    {"name": "email", "type": "VARCHAR(255)"},
                ]
            },
        },
        {
            "id": "model-1",
            "name": "CustomerAccount",
            "node_type": "model",
            "path": "models/customer.py",
            "properties": {
                "table_name": "customer_accounts",
                "fields": ["id", "email"],  # id vs customer_id drift
            },
        },
    ]

    results = detector.detect(nodes, [])
    assert len(results) > 0
    assert any("Column Identifier Naming Drift" in r.title for r in results)
    drift = results[0]
    assert drift.expected == "customer_id"
    assert drift.actual == "id"


def test_schema_mismatch_detector():
    detector = SchemaMismatchDetector()

    nodes = [
        {
            "id": "tbl-1",
            "name": "users",
            "node_type": "table",
            "path": "schema.sql",
            "properties": {
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False},
                    {"name": "age", "type": "INT", "nullable": True},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": False},
                ]
            },
        },
        {
            "id": "model-1",
            "name": "User",
            "node_type": "model",
            "path": "models/user.py",
            "properties": {
                "table_name": "users",
                "fields": [
                    {"name": "id", "type": "int", "nullable": False},
                    {"name": "age", "type": "string", "nullable": True},  # Type conflict!
                    {"name": "email", "type": "str", "nullable": True},   # Nullability drift! (SQL is NOT NULL)
                    {"name": "nickname", "type": "str", "nullable": True}, # Missing in DB!
                ],
            },
        },
    ]

    results = detector.detect(nodes, [])
    assert len(results) >= 3
    titles = [r.title for r in results]
    assert any("Data Type Mismatch" in t for t in titles)
    assert any("Nullability Drift" in t for t in titles)
    assert any("Missing DB Column" in t for t in titles)


def test_documentation_drift_detector():
    detector = DocumentationDriftDetector()

    nodes = [
        {
            "id": "svc-1",
            "name": "auth-service",
            "node_type": "service",
            "path": "services/auth",
            "properties": {},
        },
        {
            "id": "api-1",
            "name": "/api/v1/auth/login",
            "node_type": "api",
            "path": "openapi.json",
            "properties": {"path": "/api/v1/auth/login"},
        },
        {
            "id": "doc-1",
            "name": "docs/architecture.md",
            "node_type": "documentation",
            "path": "docs/architecture.md",
            "properties": {
                "content": (
                    "# Architecture\n\n"
                    "Clients authenticate using POST /api/v0/legacy/token against legacy-auth-service.\n"
                    "Then call GET /api/v1/auth/login to verify status."
                )
            },
        },
    ]

    results = detector.detect(nodes, [])
    assert len(results) >= 2
    titles = [r.title for r in results]
    assert any("POST /api/v0/legacy/token" in t for t in titles)
    assert any("legacy-auth-service" in t for t in titles)


def test_missing_documentation_detector():
    detector = MissingDocumentationDetector()

    nodes = [
        {
            "id": "s1",
            "name": "billing-service",
            "node_type": "service",
            "path": "services/billing",
            "properties": {},
        },
        {
            "id": "s2",
            "name": "auth-service",
            "node_type": "service",
            "path": "services/auth",
            "properties": {},
        },
        {
            "id": "d1",
            "name": "docs/auth.md",
            "node_type": "documentation",
            "properties": {"content": "Auth service documentation details auth-service"},
        },
    ]
    edges = [
        {
            "source_node_id": "d1",
            "target_node_id": "s2",
            "relationship_type": "documents",
        }
    ]

    results = detector.detect(nodes, edges)
    assert len(results) == 1
    assert "billing-service" in results[0].title


def test_stale_references_detector():
    detector = StaleReferencesDetector()

    nodes = [
        {
            "id": "svc-1",
            "name": "api-gateway",
            "node_type": "service",
            "path": "docker-compose.yml",
            "properties": {
                "depends_on": ["active-redis", "deleted-cache-cluster"]
            },
        },
        {
            "id": "svc-2",
            "name": "active-redis",
            "node_type": "service",
            "properties": {},
        },
    ]

    results = detector.detect(nodes, [])
    assert len(results) == 1
    assert "deleted-cache-cluster" in results[0].title


def test_contradictory_declarations_detector():
    detector = ContradictoryDeclarationsDetector()

    nodes = [
        {
            "id": "n1",
            "name": "payment-api",
            "node_type": "service",
            "path": "services/payment/Dockerfile",
            "properties": {
                "service": "payment-api",
                "exposed_ports": [8080],
            },
        },
        {
            "id": "n2",
            "name": "payment-api",
            "node_type": "service",
            "path": "docker-compose.yml",
            "properties": {
                "service": "payment-api",
                "ports": ["9000:9000"],
            },
        },
    ]

    results = detector.detect(nodes, [])
    assert len(results) == 1
    assert "Port Contradiction in Service 'payment-api'" in results[0].title
    assert results[0].metadata["ports"] == [8080, 9000]


@pytest.mark.asyncio
async def test_context_engine_end_to_end_and_api(client: AsyncClient, test_session):
    # Seed graph nodes with intentional discrepancies
    node_tbl = GraphNode(
        name="orders",
        node_type="table",
        path="schema.sql",
        properties={
            "columns": [
                {"name": "id", "type": "INT", "nullable": False},
                {"name": "total", "type": "DECIMAL(10,2)", "nullable": False},
            ]
        },
    )
    node_model = GraphNode(
        name="Order",
        node_type="model",
        path="models/order.py",
        properties={
            "table_name": "orders",
            "fields": [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "total", "type": "str", "nullable": True},  # Type & Nullability mismatch
            ],
        },
    )
    test_session.add_all([node_tbl, node_model])
    await test_session.commit()

    # Trigger analysis via API
    resp = await client.post("/api/v1/context/analyze", json={})
    assert resp.status_code == 200
    findings = resp.json()
    assert len(findings) >= 1

    # Verify listing findings
    list_resp = await client.get("/api/v1/context/findings")
    assert list_resp.status_code == 200
    all_f = list_resp.json()
    assert len(all_f) >= 1
    target_f = all_f[0]

    # Verify single finding detail
    detail_resp = await client.get(f"/api/v1/context/findings/{target_f['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "finding" in detail
    assert "related_nodes" in detail

    # Update status to resolved
    patch_resp = await client.patch(
        f"/api/v1/context/findings/{target_f['id']}",
        json={"status": "resolved"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "resolved"

    # Verify statistics
    stats_resp = await client.get("/api/v1/context/statistics")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_findings"] >= 1
    assert stats["findings_by_status"]["resolved"] >= 1
