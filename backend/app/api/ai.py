"""API routes for AI Core, Behavioral Intelligence, and Model Registry."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.agent_lab_evaluator import AgentLabEvaluator
from app.core.ai.dataset import BehaviorDatasetGenerator
from app.core.ai.experiment_tracker import ExperimentTracker
from app.core.ai.model_registry import ModelRegistryManager
from app.core.database import get_db
from app.models.ai import AIExperiment, BehaviorDatasetRecord
from app.schemas.ai import (
    DatasetGenerateRequest,
    ExperimentRunRequest,
    ModelPromoteRequest,
    PredictRequest,
)

router = APIRouter(prefix="/ai", tags=["AI Core & Behavioral Intelligence"])


@router.post("/dataset/generate", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def generate_dataset(
    req: DatasetGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate or compile a behavioral intelligence dataset with explainable provenance."""
    generator = BehaviorDatasetGenerator(seed=req.seed)
    dataset = await generator.compile_dataset(
        db=db,
        num_examples=req.num_examples,
        include_existing_runs=req.include_existing_runs,
        include_existing_scenarios=req.include_existing_scenarios,
    )

    class_counts: dict[str, int] = {}
    sources: dict[str, int] = {}
    for ex in dataset:
        c = ex["behavioral_label"]
        class_counts[c] = class_counts.get(c, 0) + 1
        s = ex["source_type"]
        sources[s] = sources.get(s, 0) + 1

    provenance_samples = [ex["label_provenance"] for ex in dataset[:5]]

    # Store metadata record in DB
    dataset_rec = BehaviorDatasetRecord(
        name=req.name,
        seed=req.seed,
        num_examples=len(dataset),
        classes_distribution=class_counts,
        provenance_summary={"sources": sources, "sample_provenance": provenance_samples},
    )
    db.add(dataset_rec)
    await db.flush()

    return {
        "status": "success",
        "data": {
            "dataset_id": str(dataset_rec.id),
            "name": req.name,
            "seed": req.seed,
            "total_examples": len(dataset),
            "classes_distribution": class_counts,
            "sources_distribution": sources,
            "provenance_notes": provenance_samples,
        },
    }


@router.get("/dataset/summary", response_model=dict[str, Any])
async def get_dataset_summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get the most recent behavioral dataset configuration and class distribution."""
    query = select(BehaviorDatasetRecord).order_by(BehaviorDatasetRecord.created_at.desc()).limit(1)
    res = await db.execute(query)
    record = res.scalar_one_or_none()

    if not record:
        # Generate on-the-fly summary if none compiled yet
        generator = BehaviorDatasetGenerator(seed=42)
        dataset = await generator.compile_dataset(db=db, num_examples=70)
        class_counts: dict[str, int] = {}
        for ex in dataset:
            c = ex["behavioral_label"]
            class_counts[c] = class_counts.get(c, 0) + 1
        return {
            "status": "success",
            "data": {
                "name": "default-ephemeral-dataset",
                "total_examples": len(dataset),
                "seed": 42,
                "classes_distribution": class_counts,
                "sources_distribution": {"ephemeral": len(dataset)},
                "provenance_notes": ["Auto-generated ephemeral dataset preview"],
            },
        }

    return {
        "status": "success",
        "data": {
            "dataset_id": str(record.id),
            "name": record.name,
            "total_examples": record.num_examples,
            "seed": record.seed,
            "classes_distribution": record.classes_distribution,
            "sources_distribution": record.provenance_summary.get("sources", {}),
            "provenance_notes": record.provenance_summary.get("sample_provenance", []),
        },
    }


@router.post("/experiments/run", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def run_experiment(
    req: ExperimentRunRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Train a baseline or sequence model, evaluate on holdout test set, and log experiment."""
    tracker = ExperimentTracker()
    try:
        experiment = await tracker.run_experiment(
            db=db,
            name=req.name,
            model_type=req.model_type,
            model_version=req.model_version,
            feature_version=req.feature_version,
            seed=req.seed,
            test_split=req.test_split,
            val_split=req.val_split,
            hyperparameters=req.hyperparameters,
            dataset_name=req.dataset_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment training failed: {str(e)}",
        )

    return {
        "status": "success",
        "data": {
            "id": str(experiment.id),
            "name": experiment.name,
            "model_type": experiment.model_type,
            "model_version": experiment.model_version,
            "feature_version": experiment.feature_version,
            "seed": experiment.seed,
            "dataset_config": experiment.dataset_config,
            "hyperparameters": experiment.hyperparameters,
            "metrics": experiment.metrics,
            "training_duration_ms": experiment.training_duration_ms,
            "artifact_path": experiment.artifact_path,
            "created_at": experiment.created_at.isoformat(),
        },
    }


@router.get("/experiments", response_model=dict[str, Any])
async def list_experiments(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List historical experiment runs with accuracy, macro-F1, and hyperparameters."""
    query = select(AIExperiment).order_by(AIExperiment.created_at.desc()).limit(limit)
    res = await db.execute(query)
    experiments = res.scalars().all()

    items = [
        {
            "id": str(e.id),
            "name": e.name,
            "model_type": e.model_type,
            "model_version": e.model_version,
            "seed": e.seed,
            "metrics": {
                "accuracy": e.metrics.get("accuracy"),
                "macro_f1": e.metrics.get("macro_f1"),
                "macro_precision": e.metrics.get("macro_precision"),
                "macro_recall": e.metrics.get("macro_recall"),
            },
            "training_duration_ms": e.training_duration_ms,
            "created_at": e.created_at.isoformat(),
        }
        for e in experiments
    ]
    return {"status": "success", "data": items}


@router.get("/experiments/{experiment_id}", response_model=dict[str, Any])
async def get_experiment_details(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve full experiment report including confusion matrix and false positive analysis."""
    query = select(AIExperiment).where(AIExperiment.id == experiment_id)
    res = await db.execute(query)
    experiment = res.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found")

    return {
        "status": "success",
        "data": {
            "id": str(experiment.id),
            "name": experiment.name,
            "model_type": experiment.model_type,
            "model_version": experiment.model_version,
            "feature_version": experiment.feature_version,
            "seed": experiment.seed,
            "dataset_config": experiment.dataset_config,
            "hyperparameters": experiment.hyperparameters,
            "metrics": experiment.metrics,
            "training_duration_ms": experiment.training_duration_ms,
            "artifact_path": experiment.artifact_path,
            "created_at": experiment.created_at.isoformat(),
        },
    }


@router.get("/models", response_model=dict[str, Any])
async def list_registered_models(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """List registered models in the model registry."""
    registry = ModelRegistryManager()
    models = await registry.list_models(db)
    items = [
        {
            "id": str(m.id),
            "name": m.name,
            "version": m.version,
            "model_type": m.model_type,
            "feature_version": m.feature_version,
            "experiment_id": str(m.experiment_id),
            "status": m.status,
            "metrics_summary": m.metrics_summary,
            "artifact_path": m.artifact_path,
            "created_at": m.created_at.isoformat(),
        }
        for m in models
    ]
    return {"status": "success", "data": items}


@router.post("/models/{model_id}/promote", response_model=dict[str, Any])
async def promote_registered_model(
    model_id: uuid.UUID,
    req: ModelPromoteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Promote or archive a registered model."""
    registry = ModelRegistryManager()
    try:
        updated = await registry.promote_model(db, model_id, target_status=req.target_status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "status": "success",
        "data": {
            "id": str(updated.id),
            "name": updated.name,
            "version": updated.version,
            "status": updated.status,
            "model_type": updated.model_type,
        },
    }


@router.post("/analyze-run/{run_id}", response_model=dict[str, Any])
async def analyze_agent_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Analyze an AgentRun, distinguishing deterministic violations from probabilistic anomalies."""
    evaluator = AgentLabEvaluator()
    try:
        analysis = await evaluator.evaluate_run(db, run_id=run_id, create_evidence=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "status": "success",
        "data": analysis.model_dump(),
    }


@router.post("/predict", response_model=dict[str, Any])
async def predict_behavior(
    req: PredictRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run model inference on custom features or tool sequences with honest uncertainty disclosure."""
    registry = ModelRegistryManager()
    champion = await registry.get_champion_model(db, model_type=req.model_type)

    if not champion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No champion model registered yet. Please train an experiment first via /api/v1/ai/experiments/run.",
        )

    model, feat_proc = registry.load_model_instance(champion)
    pred_label: str
    confidence: float
    probabilities: dict[str, float]

    if champion.model_type == "baseline_logistic":
        if not req.features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Baseline model requires 'features' dict input"
            )
        norm_x = feat_proc.transform_features(req.features)
        pred_label, confidence, probabilities = model.predict(norm_x)
    elif champion.model_type == "deep_sequence_gru":
        if not req.action_sequence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sequence GRU model requires 'action_sequence' list input",
            )
        token_ids = feat_proc.tokenize_sequence(req.action_sequence)
        pred_label, confidence, probabilities = model.predict(token_ids)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported model type '{champion.model_type}'"
        )

    is_anomaly = pred_label not in ("successful",)
    uncertainty_note = None
    if confidence < 0.60:
        uncertainty_note = f"High prediction uncertainty: model confidence is {confidence * 100:.1f}%. Output must be reviewed by an engineer."

    return {
        "status": "success",
        "data": {
            "predicted_label": pred_label,
            "confidence": confidence,
            "probabilities": probabilities,
            "is_anomaly": is_anomaly,
            "model_name": champion.name,
            "model_version": champion.version,
            "model_type": champion.model_type,
            "classification_nature": "probabilistic_model_prediction",
            "uncertainty_note": uncertainty_note,
        },
    }
