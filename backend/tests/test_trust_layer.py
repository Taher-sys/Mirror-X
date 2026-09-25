"""Tests for Phase 8: Trust Layer."""

import pytest
from httpx import AsyncClient

from app.core.trust.engine import TrustLayerEngine


def test_trust_layer_engine_decisions():
    """Verify TrustLayerEngine enforces ALLOW, DENY, and HUMAN_REVIEW_REQUIRED."""
    engine = TrustLayerEngine()

    # 1. ALLOW on standard sandbox read
    d_allow = engine.evaluate(
        principal_name="developer",
        resource_name="sandbox-orders-db",
        action_name="read",
        is_sandbox=True,
    )
    assert d_allow["result"] == "ALLOW"

    # 2. DENY on real production action (Mandate: no real production actions)
    d_deny = engine.evaluate(
        principal_name="developer",
        resource_name="production-orders-db",
        action_name="read",
        is_sandbox=False,  # Attempting production!
    )
    assert d_deny["result"] == "DENY"
    assert "Strict Sandbox Isolation Policy" in d_deny["matched_policies"]
    assert d_deny["evidence"] is not None
    assert d_deny["evidence"]["evidence_type"] == "policy_decision"

    # 3. HUMAN_REVIEW_REQUIRED on destructive operation
    d_review = engine.evaluate(
        principal_name="autonomous_agent",
        resource_name="sandbox-orders-db",
        action_name="drop_table",
        is_sandbox=True,
    )
    assert d_review["result"] == "HUMAN_REVIEW_REQUIRED"
    assert d_review["evidence"] is not None

    # 4. HUMAN_REVIEW_REQUIRED on restricted data
    d_restricted = engine.evaluate(
        principal_name="autonomous_agent",
        resource_name="sandbox-user-tokens",
        action_name="read",
        resource_classification="restricted",
        is_sandbox=True,
    )
    assert d_restricted["result"] == "HUMAN_REVIEW_REQUIRED"
    assert d_restricted["evidence"] is not None


@pytest.mark.asyncio
async def test_trust_layer_api_endpoints(client: AsyncClient):
    """Test Trust Layer REST API endpoints."""
    # 1. List policies
    pol_resp = await client.get("/api/v1/trust/policies")
    assert pol_resp.status_code == 200
    policies = pol_resp.json()["data"]
    assert len(policies) >= 3

    # 2. List permissions
    perm_resp = await client.get("/api/v1/trust/permissions")
    assert perm_resp.status_code == 200
    perms = perm_resp.json()["data"]
    assert len(perms) >= 2

    # 3. List resources (all must be sandbox)
    res_resp = await client.get("/api/v1/trust/resources")
    assert res_resp.status_code == 200
    resources = res_resp.json()["data"]
    assert all(r["is_sandbox"] for r in resources)

    # 4. Evaluate destructive action -> creates evidence & decision
    eval_resp = await client.post(
        "/api/v1/trust/evaluate",
        json={
            "principal_name": "ci_pipeline",
            "resource_name": "sandbox-orders-table",
            "action_name": "drop_table",
            "is_sandbox": True,
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()["data"]
    assert eval_data["result"] == "HUMAN_REVIEW_REQUIRED"
    assert eval_data["evidence"] is not None

    # 5. List decisions
    decisions_resp = await client.get("/api/v1/trust/decisions?result_filter=HUMAN_REVIEW_REQUIRED")
    assert decisions_resp.status_code == 200
    decisions = decisions_resp.json()["data"]
    assert len(decisions) >= 1
    decision_id = decisions[0]["id"]

    # 6. Human-in-the-loop review sign-off
    review_resp = await client.post(
        f"/api/v1/trust/decisions/{decision_id}/review",
        json={"review_status": "approved", "reviewed_by": "security_lead@mirror-x.internal"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["data"]["review_status"] == "approved"
