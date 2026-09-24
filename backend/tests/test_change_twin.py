"""Tests for Phase 5 Change Twin Git diff parser, impact engine, and APIs."""

import pytest
from httpx import AsyncClient

from app.core.changes.diff_parser import GitDiffParser
from app.core.changes.impact_engine import ChangeImpactEngine
from app.models.graph import GraphNode

SAMPLE_GIT_DIFF = """diff --git a/services/orders/main.py b/services/orders/main.py
index 1234567..89abcdef 100644
--- a/services/orders/main.py
+++ b/services/orders/main.py
@@ -10,3 +10,4 @@ def create_order(payload):
-    validate_old_syntax(payload)
+    validate_new_syntax(payload)
+    track_telemetry()
"""

SAMPLE_BREAKING_DIFF = """diff --git a/schema/orders.sql b/schema/orders.sql
index 0000000..1111111 100644
--- a/schema/orders.sql
+++ b/schema/orders.sql
@@ -5,2 +5,1 @@
-    ALTER TABLE orders DROP COLUMN legacy_status;
"""


def test_git_diff_parser():
    diffs = GitDiffParser.parse(SAMPLE_GIT_DIFF)
    assert len(diffs) == 1
    f = diffs[0]
    assert f.file_path == "services/orders/main.py"
    assert f.change_type == "modified"
    assert len(f.added_lines) == 2
    assert len(f.deleted_lines) == 1
    assert "validate_old_syntax(payload)" in f.deleted_lines[0]
    assert "validate_new_syntax(payload)" in f.added_lines[0]


def test_impact_engine_direct_and_indirect_traversal():
    nodes = [
        {
            "id": "node-orders",
            "name": "orders-service",
            "node_type": "service",
            "path": "services/orders/main.py",
        },
        {
            "id": "node-checkout",
            "name": "checkout-service",
            "node_type": "service",
            "path": "services/checkout/main.py",
        },
        {
            "id": "node-docs",
            "name": "orders-docs",
            "node_type": "documentation",
            "path": "docs/orders.md",
        },
        {
            "id": "node-auth",
            "name": "auth-service",
            "node_type": "service",
            "path": "services/auth/main.py",
        },
    ]

    edges = [
        # checkout-service calls orders-service
        {
            "id": "e1",
            "source_node_id": "node-checkout",
            "target_node_id": "node-orders",
            "relationship_type": "calls",
        },
        # orders-docs documents orders-service
        {
            "id": "e2",
            "source_node_id": "node-docs",
            "target_node_id": "node-orders",
            "relationship_type": "documents",
        },
    ]

    engine = ChangeImpactEngine()
    result = engine.analyze(SAMPLE_GIT_DIFF, nodes, edges)

    # Direct node should be orders-service
    assert len(result.direct_nodes) == 1
    assert result.direct_nodes[0].name == "orders-service"

    # Indirect nodes should include checkout-service (caller)
    indirect_names = [n.name for n in result.indirect_nodes]
    assert "checkout-service" in indirect_names
    assert "auth-service" not in indirect_names  # Unrelated service should not be impacted

    # Risk score calculation
    assert result.risk_score > 0
    assert result.risk_level in ("low", "medium", "high", "critical")
    assert "service" in result.affected_categories


def test_impact_engine_breaking_change_detection():
    nodes = [
        {
            "id": "tbl-1",
            "name": "orders",
            "node_type": "table",
            "path": "schema/orders.sql",
        },
        {
            "id": "svc-1",
            "name": "orders-service",
            "node_type": "service",
            "path": "services/orders/main.py",
        },
    ]
    edges = [
        {
            "id": "e1",
            "source_node_id": "svc-1",
            "target_node_id": "tbl-1",
            "relationship_type": "reads_from",
        }
    ]

    engine = ChangeImpactEngine()
    result = engine.analyze(SAMPLE_BREAKING_DIFF, nodes, edges)

    assert len(result.direct_nodes) == 1
    assert len(result.breaking_changes) >= 1
    assert result.breaking_changes[0].severity == "critical"
    assert "Database Column Dropped" in result.breaking_changes[0].title


@pytest.mark.asyncio
async def test_changes_api_endpoints(client: AsyncClient, test_session):
    # Seed a graph node
    svc_node = GraphNode(
        name="payment-service",
        node_type="service",
        path="services/payment/main.py",
        properties={},
    )
    test_session.add(svc_node)
    await test_session.commit()

    diff_payload = """diff --git a/services/payment/main.py b/services/payment/main.py
index 000..111 100644
--- a/services/payment/main.py
+++ b/services/payment/main.py
@@ -1 +1 @@
-def pay(): pass
+def pay(): return True
"""

    # 1. POST /api/v1/changes/impact
    post_resp = await client.post(
        "/api/v1/changes/impact",
        json={
            "title": "PR #42: Payment logic overhaul",
            "git_diff": diff_payload,
            "branch": "feature/payments",
            "author": "engineer@test.com",
        },
    )
    assert post_resp.status_code == 200
    impact_data = post_resp.json()
    assert impact_data["title"] == "PR #42: Payment logic overhaul"
    assert impact_data["direct_impact_count"] == 1
    record_id = impact_data["record_id"]

    # 2. GET /api/v1/changes
    list_resp = await client.get("/api/v1/changes")
    assert list_resp.status_code == 200
    records = list_resp.json()
    assert len(records) >= 1
    assert records[0]["id"] == record_id

    # 3. GET /api/v1/changes/{id}
    get_resp = await client.get(f"/api/v1/changes/{record_id}")
    assert get_resp.status_code == 200
    single = get_resp.json()
    assert single["title"] == "PR #42: Payment logic overhaul"
    assert single["risk_level"] in ("low", "medium", "high", "critical")
