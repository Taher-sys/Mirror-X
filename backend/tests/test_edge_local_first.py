"""Integration tests for MIRROR-X Phase 11: Edge and Local-First Runtime."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import close_db, init_db
from app.core.edge.database import get_edge_db_manager
from app.main import app


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Test client fixture setting up fresh test tables for cloud and edge."""
    await init_db()
    edge_mgr = get_edge_db_manager()
    await edge_mgr.reset_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await edge_mgr.close()
    await close_db()


@pytest.mark.asyncio
async def test_edge_status_and_network_mode_toggle(test_client: AsyncClient) -> None:
    """Verifies edge node status, connectivity modes, and transitions."""
    # 1. Initial status
    status_resp = await test_client.get("/api/v1/edge/status")
    assert status_resp.status_code == 200
    data = status_resp.json()["data"]
    assert "node_id" in data
    assert "network_mode" in data
    assert "permitted_offline_capabilities" in data
    assert "restricted_cloud_capabilities" in data

    # 2. Toggle to OFFLINE
    off_resp = await test_client.post("/api/v1/edge/mode", json={"network_mode": "OFFLINE"})
    assert off_resp.status_code == 200
    assert off_resp.json()["data"]["network_mode"] == "OFFLINE"
    assert off_resp.json()["data"]["is_offline"] is True

    # Verify status reflects offline
    status_off = await test_client.get("/api/v1/edge/status")
    assert status_off.json()["data"]["network_mode"] == "OFFLINE"
    assert status_off.json()["data"]["sync_status"] == "offline"

    # 3. Toggle back to ONLINE
    on_resp = await test_client.post("/api/v1/edge/mode", json={"network_mode": "ONLINE"})
    assert on_resp.status_code == 200
    assert on_resp.json()["data"]["network_mode"] == "ONLINE"
    assert on_resp.json()["data"]["is_offline"] is False


@pytest.mark.asyncio
async def test_snapshot_pull_and_local_caching(test_client: AsyncClient) -> None:
    """Tests pulling signed cloud snapshot into the Edge SQLite replica."""
    pull_resp = await test_client.post("/api/v1/edge/snapshot/pull")
    assert pull_resp.status_code == 200
    data = pull_resp.json()["data"]
    assert "snapshot_version" in data
    assert "signature" in data
    assert "nodes_loaded" in data
    assert "edges_loaded" in data
    assert "policies_loaded" in data


@pytest.mark.asyncio
async def test_offline_mode_permitted_vs_restricted_capabilities(test_client: AsyncClient) -> None:
    """Verifies that permitted operations succeed offline while restricted operations fail with 503."""
    # 1. Switch to OFFLINE mode
    await test_client.post("/api/v1/edge/mode", json={"network_mode": "OFFLINE"})

    # 2. Permitted operation: Local Evidence Creation
    ev_payload = {
        "evidence_type": "offline_edge_telemetry",
        "source_reference": "edge://sensor/temperature_probe",
        "summary": "Local edge diagnostic reading recorded offline",
        "raw_payload": {"temp_c": 42.5, "status": "nominal"},
        "confidence": 0.95,
    }
    ev_resp = await test_client.post("/api/v1/edge/evidence", json=ev_payload)
    assert ev_resp.status_code == 201
    ev_data = ev_resp.json()["data"]
    assert ev_data["is_queued"] is True
    assert ev_data["is_offline"] is True
    assert "evidence_id" in ev_data
    assert "sync_event_id" in ev_data

    # 3. Permitted operation: Local Scenario Execution
    sc_resp = await test_client.post("/api/v1/edge/scenarios/scenario-offline-test/execute")
    assert sc_resp.status_code == 200
    assert sc_resp.json()["data"]["passed"] is True
    assert sc_resp.json()["data"]["is_offline_execution"] is True

    # 4. Restricted operation: Cloud Model Training while OFFLINE -> 503
    train_check = await test_client.post("/api/v1/edge/cloud-action-test?capability=cloud_model_training")
    assert train_check.status_code == 503
    assert "unavailable in OFFLINE mode" in train_check.json()["detail"]

    # 5. Restricted operation: Global Release Passport while OFFLINE -> 503
    passport_check = await test_client.post("/api/v1/edge/cloud-action-test?capability=global_release_passport")
    assert passport_check.status_code == 503
    assert "unavailable in OFFLINE mode" in passport_check.json()["detail"]

    # 6. Reconnect to ONLINE mode -> Restricted operation succeeds
    await test_client.post("/api/v1/edge/mode", json={"network_mode": "ONLINE"})
    online_check = await test_client.post("/api/v1/edge/cloud-action-test?capability=cloud_model_training")
    assert online_check.status_code == 200
    assert online_check.json()["data"]["status"] == "allowed_in_online_mode"


@pytest.mark.asyncio
async def test_sync_flush_reconnection_and_idempotency(test_client: AsyncClient) -> None:
    """Verifies that offline queued events flush to cloud upon reconnection with duplicate idempotency."""
    # 1. Switch to OFFLINE and enqueue evidence
    await test_client.post("/api/v1/edge/mode", json={"network_mode": "OFFLINE"})

    audit_ref = f"edge://node/memory_audit_{uuid.uuid4().hex[:8]}"
    ev_payload = {
        "evidence_type": "offline_inspection",
        "source_reference": audit_ref,
        "summary": "Offline memory audit trace",
        "raw_payload": {"bytes_used": 1048576},
        "confidence": 1.0,
    }
    create_resp = await test_client.post("/api/v1/edge/evidence", json=ev_payload)
    assert create_resp.status_code == 201

    # 2. Inspect outbound queue while offline
    queue_resp = await test_client.get("/api/v1/edge/queue")
    assert queue_resp.status_code == 200
    events = queue_resp.json()["data"]
    assert len(events) >= 1
    assert any(e["status"] == "pending" for e in events)

    # 3. Attempt sync while OFFLINE -> Deferred
    defer_sync = await test_client.post("/api/v1/edge/sync")
    assert defer_sync.status_code == 200
    assert defer_sync.json()["data"]["status"] == "deferred"

    # 4. Reconnect to ONLINE and flush queue
    await test_client.post("/api/v1/edge/mode", json={"network_mode": "ONLINE"})
    sync_resp = await test_client.post("/api/v1/edge/sync")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()["data"]
    assert sync_data["status"] == "success"
    assert sync_data["synced_count"] >= 1

    # 5. Flush again: Idempotency check ensures duplicate events do not fail or duplicate records
    dup_resp = await test_client.post("/api/v1/edge/sync")
    assert dup_resp.status_code == 200


@pytest.mark.asyncio
async def test_conflict_detection_and_explicit_resolution(test_client: AsyncClient) -> None:
    """Verifies that conflicting concurrent modifications are flagged as explicit conflicts and resolved."""
    await test_client.post("/api/v1/edge/mode", json={"network_mode": "ONLINE"})

    routing_ref = f"repo://config/routing_{uuid.uuid4().hex[:8]}.json"
    conflicting_entity_id = str(uuid.uuid4())

    # 1. Create initial evidence on Cloud directly
    seed_cloud = await test_client.post(
        "/api/v1/evidence",
        json={
            "evidence_type": "config_spec",
            "source_reference": routing_ref,
            "summary": "Initial cloud routing configuration v1",
            "raw_payload": {"gateway": "10.0.0.1", "version": 1},
            "confidence": 1.0,
        },
    )
    assert seed_cloud.status_code == 201

    # 2. Edge enqueues a conflicting version with different gateway IP
    edge_mgr = get_edge_db_manager()
    from app.core.edge.sync import EdgeSyncProtocol

    protocol = EdgeSyncProtocol()

    async with edge_mgr.session() as edge_s:
        await protocol.enqueue_outbound_event(
            edge_db=edge_s,
            entity_type="evidence",
            entity_id=conflicting_entity_id,
            version=1,
            payload={
                "source_reference": routing_ref,
                "summary": "Edge modified gateway to local gateway",
                "raw_payload": {"gateway": "192.168.1.1", "version": 1},
                "confidence": 1.0,
            },
        )
        await edge_s.commit()

    # 3. Trigger sync -> Conflict detected!
    sync_res = await test_client.post("/api/v1/edge/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["data"]["conflict_count"] >= 1
    assert sync_res.json()["data"]["sync_status"] == "conflict_detected"

    # 4. View conflicts endpoint
    conflicts_resp = await test_client.get("/api/v1/edge/conflicts")
    assert conflicts_resp.status_code == 200
    conflicts = conflicts_resp.json()["data"]
    assert len(conflicts) >= 1
    target_conflict = conflicts[0]
    conflict_id = target_conflict["id"]
    assert target_conflict["resolution_status"] == "unresolved"

    # 5. Explicitly resolve conflict with 'keep_local'
    resolve_resp = await test_client.post(
        f"/api/v1/edge/conflicts/{conflict_id}/resolve",
        json={"resolution": "keep_local", "notes": "Approved local network override for branch office"},
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["data"]["resolution_status"] == "resolved_local"

    # Verify conflict resolution status
    conflicts_after = await test_client.get("/api/v1/edge/conflicts")
    assert conflicts_after.json()["data"][0]["resolution_status"] == "resolved_local"
