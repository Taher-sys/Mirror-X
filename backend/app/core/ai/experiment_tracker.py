"""Experiment Tracker and Training Pipeline for Behavioral Intelligence.

Coordinates reproducible dataset compilation, deterministic feature extraction, model
training, holdout test evaluation (precision, recall, F1, confusion matrix, false positives),
and artifact serialization.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.baseline_model import (
    BaselineLogisticClassifier,
    compute_metrics,
    train_val_test_split,
)
from app.core.ai.dataset import BEHAVIOR_LABELS, BehaviorDatasetGenerator
from app.core.ai.features import BehavioralFeatureExtractor
from app.core.ai.sequence_model import SequenceGRUClassifier
from app.models.ai import AIExperiment, AIModelRegistry

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "models"


class ExperimentTracker:
    """Manages experiment runs, model training, evaluation metrics, and artifact persistence."""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def run_experiment(
        self,
        db: AsyncSession,
        name: str,
        model_type: str = "baseline_logistic",
        model_version: str = "1.0.0",
        feature_version: str = "v1.0",
        seed: int = 42,
        test_split: float = 0.2,
        val_split: float = 0.15,
        hyperparameters: dict[str, Any] | None = None,
        dataset_name: str = "behavior-dataset-v1",
        num_examples: int = 150,
    ) -> AIExperiment:
        """Execute a complete training run with holdout evaluation and artifact logging."""
        hp = hyperparameters or {}
        learning_rate = float(hp.get("learning_rate", 0.05 if model_type == "baseline_logistic" else 0.01))
        epochs = int(hp.get("epochs", 80 if model_type == "baseline_logistic" else 40))
        l2_reg = float(hp.get("l2_reg", 0.001))
        embedding_dim = int(hp.get("embedding_dim", 16))
        hidden_dim = int(hp.get("hidden_dim", 24))

        start_time = time.perf_counter()

        # 1. Compile dataset
        generator = BehaviorDatasetGenerator(seed=seed)
        dataset = await generator.compile_dataset(
            db=db,
            num_examples=num_examples,
            include_existing_runs=True,
            include_existing_scenarios=True,
        )

        # 2. Partition dataset
        train_data, val_data, test_data = train_val_test_split(
            dataset,
            test_ratio=test_split,
            val_ratio=val_split,
            seed=seed,
        )

        # 3. Fit feature extractor & vocab
        extractor = BehavioralFeatureExtractor()
        extractor.build_vocab_from_examples(dataset)
        raw_train_features = [extractor.extract_raw_features(ex) for ex in train_data]
        extractor.fit_scaler(raw_train_features)

        # Prepare X and y for train, val, test
        train_labels = [ex["behavioral_label"] for ex in train_data]
        val_labels = [ex["behavioral_label"] for ex in val_data]
        test_labels = [ex["behavioral_label"] for ex in test_data]

        experiment_id = uuid.uuid4()
        artifact_path = self.artifacts_dir / f"{experiment_id}.json"

        # 4. Train Model
        metrics: dict[str, Any] = {}
        if model_type == "baseline_logistic":
            X_train = [extractor.transform_features(raw) for raw in raw_train_features]
            X_val = [extractor.transform_features(extractor.extract_raw_features(ex)) for ex in val_data]
            X_test = [extractor.transform_features(extractor.extract_raw_features(ex)) for ex in test_data]

            classifier = BaselineLogisticClassifier(
                num_features=len(extractor.feature_keys),
                classes=BEHAVIOR_LABELS,
                learning_rate=learning_rate,
                l2_reg=l2_reg,
                seed=seed,
            )
            classifier.fit(X_train, train_labels, X_val, val_labels, epochs=epochs)

            # Test predictions
            test_preds = [classifier.predict(x)[0] for x in X_test]
            metrics = compute_metrics(test_labels, test_preds, BEHAVIOR_LABELS)

            # Feature coefficients (Explainability)
            metrics["feature_coefficients"] = classifier.get_feature_coefficients(extractor.feature_keys)

            # Serialize model artifact
            model_dict = classifier.to_dict()
            model_dict["scaler_means"] = extractor.feature_means
            model_dict["scaler_stds"] = extractor.feature_stds
            model_dict["feature_keys"] = extractor.feature_keys
            artifact_path.write_text(json.dumps(model_dict, indent=2))

        elif model_type == "deep_sequence_gru":
            tokens_train = [extractor.tokenize_sequence(ex.get("action_sequence", [])) for ex in train_data]
            tokens_val = [extractor.tokenize_sequence(ex.get("action_sequence", [])) for ex in val_data]
            tokens_test = [extractor.tokenize_sequence(ex.get("action_sequence", [])) for ex in test_data]

            gru_model = SequenceGRUClassifier(
                vocab_size=len(extractor.vocab),
                embedding_dim=embedding_dim,
                hidden_dim=hidden_dim,
                classes=BEHAVIOR_LABELS,
                learning_rate=learning_rate,
                seed=seed,
            )
            gru_model.fit(tokens_train, train_labels, tokens_val, val_labels, epochs=epochs)

            # Test predictions
            test_preds = [gru_model.predict(seq)[0] for seq in tokens_test]
            metrics = compute_metrics(test_labels, test_preds, BEHAVIOR_LABELS)

            # Serialize sequence model artifact
            gru_dict = gru_model.to_dict()
            gru_dict["vocab"] = extractor.vocab
            artifact_path.write_text(json.dumps(gru_dict, indent=2))

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 5. Persist AIExperiment record
        experiment = AIExperiment(
            id=experiment_id,
            name=name,
            model_type=model_type,
            model_version=model_version,
            feature_version=feature_version,
            seed=seed,
            dataset_config={
                "dataset_name": dataset_name,
                "total_examples": len(dataset),
                "train_count": len(train_data),
                "val_count": len(val_data),
                "test_count": len(test_data),
                "test_split": test_split,
                "val_split": val_split,
            },
            hyperparameters={
                "learning_rate": learning_rate,
                "epochs": epochs,
                "l2_reg": l2_reg,
                "embedding_dim": embedding_dim,
                "hidden_dim": hidden_dim,
            },
            metrics=metrics,
            training_duration_ms=duration_ms,
            artifact_path=str(artifact_path),
            notes=f"Trained on {len(train_data)} examples with test macro-F1: {metrics.get('macro_f1', 0.0)}",
        )
        db.add(experiment)

        # 6. Register model candidate in AIModelRegistry
        model_reg = AIModelRegistry(
            id=uuid.uuid4(),
            name=f"mirrorx-{model_type}",
            version=model_version,
            model_type=model_type,
            feature_version=feature_version,
            experiment_id=experiment.id,
            status="candidate",
            metrics_summary={
                "accuracy": metrics.get("accuracy", 0.0),
                "macro_f1": metrics.get("macro_f1", 0.0),
                "macro_precision": metrics.get("macro_precision", 0.0),
                "macro_recall": metrics.get("macro_recall", 0.0),
            },
            artifact_path=str(artifact_path),
        )
        db.add(model_reg)
        await db.flush()

        return experiment
