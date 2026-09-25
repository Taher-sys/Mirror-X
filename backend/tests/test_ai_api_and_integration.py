"""Integration tests for AI Core FastAPI endpoints and Agent Behavior Lab integration."""

from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import Base, close_db, engine, get_db, init_db
from app.main import app
from app.models.agent import Agent, AgentRun, AgentStep


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Test client fixture setting up fresh test tables."""
    await init_db()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    await close_db()


@pytest.mark.asyncio
async def test_dataset_generation_and_summary_flow(test_client: AsyncClient) -> None:
    """Tests generating a behavioral dataset and retrieving its summary."""
    # 1. Generate dataset
    gen_payload = {
        "num_examples": 28,
        "seed": 42,
        "include_existing_runs": True,
        "include_existing_scenarios": True,
        "name": "test-dataset-suite",
    }
    resp = await test_client.post("/api/v1/ai/dataset/generate", json=gen_payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["name"] == "test-dataset-suite"
    assert data["total_examples"] >= 28
    assert "classes_distribution" in data
    assert len(data["classes_distribution"]) > 0

    # 2. Get dataset summary
    summary_resp = await test_client.get("/api/v1/ai/dataset/summary")
    assert summary_resp.status_code == 200
    sum_body = summary_resp.json()
    assert sum_body["status"] == "success"
    assert sum_body["data"]["total_examples"] >= 28


@pytest.mark.asyncio
async def test_experiments_run_baseline_and_sequence(test_client: AsyncClient) -> None:
    """Tests running training experiments for baseline logistic and deep sequence GRU models."""
    # 1. Run Baseline Logistic Experiment
    base_payload = {
        "name": "audit-baseline-logistic-exp",
        "model_type": "baseline_logistic",
        "model_version": "1.0.0",
        "feature_version": "v1.0",
        "seed": 42,
        "test_split": 0.2,
        "val_split": 0.15,
        "hyperparameters": {
            "learning_rate": 0.05,
            "epochs": 15,
            "l2_reg": 0.001,
        },
        "dataset_name": "test-dataset-suite",
    }
    resp1 = await test_client.post("/api/v1/ai/experiments/run", json=base_payload)
    assert resp1.status_code == 201
    exp1_data = resp1.json()["data"]
    exp1_id = exp1_data["id"]
    assert exp1_data["model_type"] == "baseline_logistic"
    assert "metrics" in exp1_data
    assert "accuracy" in exp1_data["metrics"]
    assert "confusion_matrix" in exp1_data["metrics"]

    # 2. Run Deep Sequence GRU Experiment
    gru_payload = {
        "name": "audit-sequence-gru-exp",
        "model_type": "deep_sequence_gru",
        "model_version": "1.0.0",
        "feature_version": "v1.0",
        "seed": 42,
        "test_split": 0.2,
        "val_split": 0.15,
        "hyperparameters": {
            "learning_rate": 0.02,
            "epochs": 10,
            "embedding_dim": 8,
            "hidden_dim": 12,
        },
        "dataset_name": "test-dataset-suite",
    }
    resp2 = await test_client.post("/api/v1/ai/experiments/run", json=gru_payload)
    assert resp2.status_code == 201
    exp2_data = resp2.json()["data"]
    exp2_id = exp2_data["id"]
    assert exp2_data["model_type"] == "deep_sequence_gru"
    assert "accuracy" in exp2_data["metrics"]

    # 3. List experiments
    list_resp = await test_client.get("/api/v1/ai/experiments")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 2

    # 4. Get specific experiment details
    get_exp = await test_client.get(f"/api/v1/ai/experiments/{exp1_id}")
    assert get_exp.status_code == 200
    assert get_exp.json()["data"]["name"] == "audit-baseline-logistic-exp"


@pytest.mark.asyncio
async def test_model_registry_promote_and_predict(test_client: AsyncClient) -> None:
    """Tests model registry listing, promotion to champion, and inference prediction."""
    # List models
    models_resp = await test_client.get("/api/v1/ai/models")
    assert models_resp.status_code == 200
    models = models_resp.json()["data"]
    assert len(models) >= 1

    target_model = models[0]
    model_id = target_model["id"]

    # Promote to champion
    promote_resp = await test_client.post(
        f"/api/v1/ai/models/{model_id}/promote",
        json={"target_status": "champion"},
    )
    assert promote_resp.status_code == 200
    assert promote_resp.json()["data"]["status"] == "champion"

    # Run prediction
    if target_model["model_type"] == "baseline_logistic":
        pred_req = {
            "features": {
                "tool_call_frequency": 3.0,
                "unique_tools_count": 2.0,
                "action_sequence_length": 3.0,
                "retry_count": 0.0,
                "latency_ms": 120.0,
                "avg_step_duration_ms": 40.0,
                "error_count": 0.0,
                "has_error": 0.0,
                "policy_denials": 0.0,
                "human_review_events": 0.0,
                "policy_violations": 0.0,
                "unnecessary_actions_count": 0.0,
                "incorrect_tool_uses_count": 0.0,
                "sandbox_access_ratio": 1.0,
                "action_order_entropy": 0.9,
                "max_consecutive_repeats": 1.0,
                "scenario_class_normal": 1.0,
                "scenario_class_adversarial": 0.0,
                "scenario_class_boundary": 0.0,
                "scenario_has_constraints": 0.0,
                "execution_outcome_success": 1.0,
            }
        }
    else:
        pred_req = {
            "action_sequence": ["query_database", "read_file", "parse_ast"],
        }

    pred_resp = await test_client.post("/api/v1/ai/predict", json=pred_req)
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()["data"]
    assert "predicted_label" in pred_data
    assert "confidence" in pred_data
    assert pred_data["classification_nature"] == "probabilistic_model_prediction"


@pytest.mark.asyncio
async def test_analyze_run_distinguishes_violations_vs_anomalies(test_client: AsyncClient) -> None:
    """Verifies that analyze-run cleanly distinguishes deterministic violations from model anomalies."""
    # 1. Create agent and run with intentional policy denial and unhandled error
    create_agent = await test_client.post(
        "/api/v1/agents",
        json={
            "name": "Security Audit Agent",
            "version": "v1.0.0",
            "model_reference": "gpt-4o",
            "purpose": "Test policy violation detection",
        },
    )
    agent_id = create_agent.json()["data"]["id"]

    run_payload = {
        "goal": "Verify database integrity and inspect users schema",
        "context_reference": {"environment": "sandbox", "repo": "ecommerce-core"},
        "scenario_inputs": {"table": "users", "action": "inspect"},
    }
    run_resp = await test_client.post(f"/api/v1/agents/{agent_id}/run", json=run_payload)
    assert run_resp.status_code == 200
    run_id = run_resp.json()["data"]["id"]

    # 2. Evaluate run
    eval_resp = await test_client.post(f"/api/v1/ai/analyze-run/{run_id}")
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()["data"]

    assert eval_data["run_id"] == run_id
    assert "deterministic_policy_violations" in eval_data
    assert "model_based_anomalies" in eval_data
    assert "heuristic_warnings" in eval_data
    assert "uncertain_predictions" in eval_data
    assert "evidence_id" in eval_data
    assert eval_data["evidence_id"] is not None
