"""Tests for Phase 9: Evidence Ledger and Release Passport."""

import pytest
from httpx import AsyncClient

from app.core.releases.passport_engine import ReleasePassportEngine
from app.models.evidence import EvidenceRecord


def test_evidence_hash_provenance():
    """Verify SHA-256 tamper-evident provenance calculation."""
    payload = {"query": "SELECT * FROM orders", "result_count": 42}
    source = "database://sandbox-orders"
    hash1 = EvidenceRecord.calculate_hash(payload, source)
    hash2 = EvidenceRecord.calculate_hash(payload, source)
    assert hash1 == hash2
    assert len(hash1) == 64

    # Tampered payload yields distinct hash
    tampered_payload = {"query": "SELECT * FROM orders", "result_count": 9999}
    tampered_hash = EvidenceRecord.calculate_hash(tampered_payload, source)
    assert hash1 != tampered_hash


def test_release_passport_statuses_and_uncertainty():
    """Verify ReleasePassportEngine correctly derives all 5 statuses and discloses uncertainty."""
    # 1. NOT_EVALUATED on empty inputs
    p_empty = ReleasePassportEngine.generate_passport("v1.0.0-rc1")
    assert p_empty["overall_status"] == "NOT_EVALUATED"
    assert "No Git changes or PRs" in p_empty["uncertainty_notes"]

    # 2. FAIL on critical open findings
    p_fail = ReleasePassportEngine.generate_passport(
        "v1.0.0-rc2",
        findings=[{"severity": "critical", "status": "open"}],
    )
    assert p_fail["overall_status"] == "FAIL"
    assert "critical architecture/schema discrepancies" in p_fail["uncertainty_notes"]

    # 3. HUMAN_REVIEW_REQUIRED on breaking changes or agent policy violations
    p_review = ReleasePassportEngine.generate_passport(
        "v1.0.0-rc3",
        changes=[{"impact_summary": {"breaking_changes": [{"title": "Drop column"}]}}],
    )
    assert p_review["overall_status"] == "HUMAN_REVIEW_REQUIRED"

    # 4. WARNING on high-severity findings
    p_warn = ReleasePassportEngine.generate_passport(
        "v1.0.0-rc4",
        findings=[{"severity": "high", "status": "open"}],
        scenarios=[
            {"status": "passed"},
            {"status": "passed"},
            {"status": "passed"},
        ],
    )
    assert p_warn["overall_status"] == "WARNING"

    # 5. PASS when all verification domains pass cleanly
    p_pass = ReleasePassportEngine.generate_passport(
        "v1.0.0",
        changes=[{"impact_summary": {"breaking_changes": []}, "risk_score": 10.0}],
        findings=[{"severity": "low", "status": "resolved"}],
        scenarios=[
            {"status": "passed", "scenario_class": "normal"},
            {"status": "passed", "scenario_class": "boundary"},
            {"status": "passed", "scenario_class": "adversarial"},
        ],
        agent_runs=[{"metrics": {"successful_completion": True, "policy_violations_count": 0}}],
        policy_decisions=[{"result": "ALLOW"}],
        evidence_records=[{"evidence_type": "api_contract", "source_reference": "/api/v1/orders"}],
    )
    assert p_pass["overall_status"] == "PASS"
    assert len(p_pass["passport_hash"]) == 64


@pytest.mark.asyncio
async def test_evidence_and_release_api(client: AsyncClient):
    """Test Evidence Ledger and Release Passport REST APIs."""
    # 1. Create Evidence
    evi_resp = await client.post(
        "/api/v1/evidence",
        json={
            "evidence_type": "api_contract",
            "source_reference": "openapi://orders/v1",
            "summary": "Verified OpenAPI schema contract adherence",
            "raw_payload": {"endpoint": "/api/v1/orders", "method": "POST", "status": 200},
            "confidence": 1.0,
        },
    )
    assert evi_resp.status_code == 201
    evi_data = evi_resp.json()["data"]
    evi_id = evi_data["id"]
    assert len(evi_data["hash_signature"]) == 64

    # 2. Get Evidence and verify tamper check
    get_evi = await client.get(f"/api/v1/evidence/{evi_id}")
    assert get_evi.status_code == 200
    assert get_evi.json()["data"]["id"] == evi_id

    # 3. Create Release candidate
    rel_resp = await client.post(
        "/api/v1/releases",
        json={
            "name": "Sprint 24 Release",
            "version": "v1.2.0-rc1",
            "target_environment": "staging",
            "commit_hash": "a1b2c3d4e5f678901234567890abcdef12345678",
            "change_ids": [],
        },
    )
    assert rel_resp.status_code == 201
    release_id = rel_resp.json()["data"]["id"]

    # 4. Issue Release Passport
    passport_resp = await client.post(f"/api/v1/releases/{release_id}/passport")
    assert passport_resp.status_code == 200
    pass_data = passport_resp.json()["data"]
    assert "overall_status" in pass_data
    assert "code_change_analysis" in pass_data
    assert "context_findings" in pass_data
    assert "scenario_testing" in pass_data
    assert "agent_testing" in pass_data
    assert "policy_validation" in pass_data
    assert "evidence_completeness" in pass_data
    assert "uncertainty_notes" in pass_data
    assert len(pass_data["passport_hash"]) == 64

    # 5. Fetch issued passport
    get_pass = await client.get(f"/api/v1/releases/{release_id}/passport")
    assert get_pass.status_code == 200
    assert get_pass.json()["data"]["passport_hash"] == pass_data["passport_hash"]
