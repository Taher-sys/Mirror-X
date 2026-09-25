"""Tests for Phase 6: Synthetic Scenario Engine."""

import pytest
from httpx import AsyncClient

from app.core.scenarios.generator import VALID_SCENARIO_CLASSES, SyntheticScenarioEngine


@pytest.mark.asyncio
async def test_scenario_classes_generation():
    """Verify that all 10 scenario classes generate valid reproducible scenarios."""
    engine = SyntheticScenarioEngine(seed=42)
    for s_class in VALID_SCENARIO_CLASSES:
        scenario = engine.generate(
            target_name="OrdersService",
            source_type="api",
            scenario_class=s_class,
            seed=100,
        )
        assert scenario["scenario_class"] == s_class
        assert "scenario_id" in scenario
        assert "initial_state" in scenario
        assert "generated_inputs" in scenario
        assert "expected_constraints" in scenario
        assert len(scenario["participating_resources"]) > 0
        assert len(scenario["applicable_policies"]) > 0
        assert scenario["metadata"]["seed"] == 100


def test_seed_reproducibility():
    """Verify that same seed reproduces identical inputs and constraints."""
    e1 = SyntheticScenarioEngine(seed=999)
    e2 = SyntheticScenarioEngine(seed=111)

    # Same seed 777 passed to both
    scen_a = e1.generate(target_name="PaymentAPI", source_type="api", scenario_class="boundary", seed=777)
    scen_b = e2.generate(target_name="PaymentAPI", source_type="api", scenario_class="boundary", seed=777)

    assert scen_a["generated_inputs"] == scen_b["generated_inputs"]
    assert scen_a["expected_constraints"] == scen_b["expected_constraints"]
    assert scen_a["initial_state"] == scen_b["initial_state"]


def test_scenario_execution():
    """Verify scenario execution in the sandbox harness."""
    engine = SyntheticScenarioEngine(seed=42)
    scenario = engine.generate(target_name="AuthService", source_type="api", scenario_class="adversarial", seed=42)
    result = engine.execute_scenario(scenario)

    assert result["passed"] is True
    assert result["actual_decision"] == "DENY"
    assert result["evidence_generated"] is True
    assert result["execution_duration_ms"] > 0


@pytest.mark.asyncio
async def test_scenario_api_endpoints(client: AsyncClient):
    """Test scenario REST API endpoints using the standard test client."""
    # 1. Generate scenario
    gen_resp = await client.post(
        "/api/v1/scenarios/generate",
        json={
            "target_name": "OrdersAPI",
            "source_type": "api",
            "scenario_class": "boundary",
            "seed": 42,
        },
    )
    assert gen_resp.status_code == 201
    data = gen_resp.json()["data"]
    scen_id = data["id"]
    assert data["scenario_class"] == "boundary"
    assert data["seed"] == 42

    # 2. Retrieve scenario
    get_resp = await client.get(f"/api/v1/scenarios/{scen_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == scen_id

    # 3. Execute scenario
    exec_resp = await client.post(f"/api/v1/scenarios/{scen_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()["data"]
    assert exec_data["passed"] is True

    # 4. List scenarios
    list_resp = await client.get("/api/v1/scenarios?scenario_class=boundary")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert len(items) >= 1

    # 5. Batch generation
    batch_resp = await client.post("/api/v1/scenarios/batch?target_name=InventoryService&seed=500")
    assert batch_resp.status_code == 200
    batch_items = batch_resp.json()["data"]
    assert len(batch_items) == 10
