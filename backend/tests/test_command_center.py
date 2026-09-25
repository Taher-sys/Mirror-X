"""Tests for Command Center API endpoints and models."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.project import Project
from app.models.repository import Repository


@pytest.mark.asyncio
async def test_system_status_and_summary_empty(client: AsyncClient):
    """Test system status and summary endpoints when database is empty."""
    # Test status endpoint
    status_resp = await client.get("/api/v1/system/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()["data"]
    assert status_data["status"] == "healthy"
    assert status_data["database_connected"] is True
    assert status_data["database_latency_ms"] >= 0.0

    # Test summary endpoint with empty database
    summary_resp = await client.get("/api/v1/system/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()["data"]
    assert summary_data["repositories_count"] == 0
    assert summary_data["services_count"] == 0
    assert summary_data["findings_count"] == 0
    assert summary_data["system_status"] == "uninitialized"
    assert summary_data["findings_by_severity"]["critical"] == 0


@pytest.mark.asyncio
async def test_repositories_crud_and_stats(client: AsyncClient, test_session: AsyncSession):
    """Test repository listing, creation, and count reflection."""
    # Create org and project
    org = Organization(name="Acme Corp")
    test_session.add(org)
    await test_session.flush()

    proj = Project(name="Project Alpha", organization_id=org.id)
    test_session.add(proj)
    await test_session.commit()

    # List repositories (empty)
    list_resp = await client.get("/api/v1/repositories")
    assert list_resp.status_code == 200
    assert list_resp.json()["data"] == []
    assert list_resp.json()["meta"]["total"] == 0

    # Create repository
    payload = {
        "name": "mirror-x",
        "url": "https://github.com/Taher-sys/Mirror-X",
        "default_branch": "main",
        "language": "TypeScript",
        "status": "active",
        "project_id": str(proj.id),
    }
    create_resp = await client.post("/api/v1/repositories", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()["data"]
    assert created_data["name"] == "mirror-x"
    assert created_data["services_count"] == 0

    # List again
    list_resp2 = await client.get("/api/v1/repositories")
    assert list_resp2.status_code == 200
    assert len(list_resp2.json()["data"]) == 1
    assert list_resp2.json()["meta"]["total"] == 1

    # Check that activity was logged
    act_resp = await client.get("/api/v1/activities")
    assert act_resp.status_code == 200
    activities = act_resp.json()["data"]
    assert len(activities) >= 1
    assert activities[0]["action"] == "repository_connected"


@pytest.mark.asyncio
async def test_services_and_findings_flow(client: AsyncClient, test_session: AsyncSession):
    """Test service registration, findings creation, and summary calculation."""
    org = Organization(name="Test Org")
    test_session.add(org)
    await test_session.flush()

    proj = Project(name="Test Project", organization_id=org.id)
    test_session.add(proj)
    await test_session.flush()

    repo = Repository(
        name="backend-repo",
        url="https://github.com/org/backend-repo",
        project_id=proj.id,
    )
    test_session.add(repo)
    await test_session.commit()

    # Register service
    svc_payload = {
        "name": "payment-api",
        "service_type": "api",
        "status": "healthy",
        "runtime": "Python 3.11",
        "version": "v1.2.0",
        "repository_id": str(repo.id),
    }
    svc_resp = await client.post("/api/v1/services", json=svc_payload)
    assert svc_resp.status_code == 201
    svc_data = svc_resp.json()["data"]
    assert svc_data["name"] == "payment-api"

    # Create findings with different severities
    f1_payload = {
        "title": "API Drift: /v1/checkout schema mismatch",
        "finding_type": "schema_mismatch",
        "severity": "critical",
        "confidence": 0.98,
        "description": "Request body expects 'amount_cents' but documentation specifies 'amount'",
        "repository_id": str(repo.id),
        "service_id": str(svc_data["id"]),
    }
    f1_resp = await client.post("/api/v1/findings", json=f1_payload)
    assert f1_resp.status_code == 201

    f2_payload = {
        "title": "Missing docstring on authenticate()",
        "finding_type": "missing_documentation",
        "severity": "low",
        "confidence": 0.85,
        "description": "Public handler method authenticate() has no markdown docstring",
        "repository_id": str(repo.id),
    }
    f2_resp = await client.post("/api/v1/findings", json=f2_payload)
    assert f2_resp.status_code == 201

    # Check findings summary
    summary_resp = await client.get("/api/v1/findings/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()["data"]
    assert summary_data["critical"] == 1
    assert summary_data["low"] == 1
    assert summary_data["total"] == 2

    # Verify system summary now reflects real counts and degraded status due to critical finding
    sys_summary = await client.get("/api/v1/system/summary")
    assert sys_summary.status_code == 200
    sys_data = sys_summary.json()["data"]
    assert sys_data["repositories_count"] == 1
    assert sys_data["services_count"] == 1
    assert sys_data["findings_count"] == 2
    assert sys_data["system_status"] == "degraded"  # Because critical finding exists
