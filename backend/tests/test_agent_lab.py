"""Tests for Phase 7: Agent Behavior Lab."""

import pytest
from httpx import AsyncClient

from app.core.agents.comparison import AgentVersionComparator
from app.core.agents.lab_engine import AgentBehaviorLabEngine


def test_agent_behavior_lab_engine():
    """Verify controlled agent execution records all mandatory telemetry."""
    lab = AgentBehaviorLabEngine()
    run = lab.execute_run(
        agent_name="OpsNavigator",
        agent_version="v1.0.0",
        model_reference="gpt-4o",
        goal="Inspect and update checkout service status",
        context_reference={"service": "checkout"},
    )

    # Mandatory fields
    assert run["agent_version"] == "v1.0.0"
    assert run["goal"] == "Inspect and update checkout service status"
    assert run["context_reference"] == {"service": "checkout"}
    assert run["model_reference"] == "gpt-4o"
    assert len(run["plan"]) > 0
    assert len(run["steps"]) > 0
    assert run["trace_id"].startswith("trace_")
    assert "timings" in run
    assert "result" in run

    # Verify step telemetry
    first_step = run["steps"][0]
    assert "step_number" in first_step
    assert "thought" in first_step
    assert "tool_call" in first_step
    assert "arguments" in first_step
    assert "tool_output" in first_step
    assert "policy_check" in first_step
    assert first_step["duration_ms"] > 0

    # Measurable behavior metrics
    metrics = run["metrics"]
    assert "successful_completion" in metrics
    assert "correct_tool_selection_count" in metrics
    assert "incorrect_tool_use_count" in metrics
    assert "unnecessary_actions_count" in metrics
    assert "policy_violations_count" in metrics
    assert "error_count" in metrics
    assert "latency_ms" in metrics
    assert "retry_count" in metrics


def test_version_comparator():
    """Verify version comparison evaluates multidimensional behaviors without an arbitrary intelligence score."""
    lab = AgentBehaviorLabEngine()
    base_run = lab.execute_run("Architect", "v1.0.0", "gpt-4o", "Analyze order pipeline")
    cand_run = lab.execute_run("Architect", "v1.1.0", "gpt-4o", "Analyze order pipeline")

    comparison = AgentVersionComparator.compare_runs(base_run, cand_run)

    assert comparison["baseline_version"] == "v1.0.0"
    assert comparison["candidate_version"] == "v1.1.0"
    matrix = comparison["behavioral_matrix"]

    assert "successful_completion" in matrix
    assert "correct_tool_selection" in matrix
    assert "incorrect_tool_use" in matrix
    assert "unnecessary_actions" in matrix
    assert "policy_violations" in matrix
    assert "error_count" in matrix
    assert "latency_ms" in matrix
    assert "retry_count" in matrix
    assert "score" not in comparison  # No arbitrary single intelligence score!


@pytest.mark.asyncio
async def test_agent_lab_api_endpoints(client: AsyncClient):
    """Test Agent Behavior Lab REST API endpoints."""
    # 1. Create Agent
    create_resp = await client.post(
        "/api/v1/agents",
        json={
            "name": "ReliabilityAgent",
            "version": "v1.0.0",
            "model_reference": "claude-3-5-sonnet",
            "purpose": "Autonomous reliability and schema drift monitor",
        },
    )
    assert create_resp.status_code == 201
    agent_id = create_resp.json()["data"]["id"]

    # 2. List tools
    tools_resp = await client.get("/api/v1/agents/tools")
    assert tools_resp.status_code == 200
    tools = tools_resp.json()["data"]
    assert len(tools) >= 5

    # 3. Trigger Agent Run
    run1_resp = await client.post(
        f"/api/v1/agents/{agent_id}/run",
        json={"goal": "Verify database schema for orders service"},
    )
    assert run1_resp.status_code == 200
    run1_data = run1_resp.json()["data"]
    run1_id = run1_data["id"]
    assert len(run1_data["steps"]) >= 2
    assert run1_data["trace_id"].startswith("trace_")

    # 4. Trigger second run for comparison
    run2_resp = await client.post(
        f"/api/v1/agents/{agent_id}/run",
        json={"goal": "Verify database schema for orders service v2"},
    )
    assert run2_resp.status_code == 200
    run2_id = run2_resp.json()["data"]["id"]

    # 5. List runs
    runs_list = await client.get(f"/api/v1/agents/runs/list?agent_id={agent_id}")
    assert runs_list.status_code == 200
    assert len(runs_list.json()["data"]) >= 2

    # 6. Compare runs
    compare_resp = await client.post(
        "/api/v1/agents/compare",
        json={"baseline_run_id": run1_id, "candidate_run_id": run2_id},
    )
    assert compare_resp.status_code == 200
    comp_data = compare_resp.json()["data"]
    assert "behavioral_matrix" in comp_data
    assert "unnecessary_actions" in comp_data["behavioral_matrix"]
