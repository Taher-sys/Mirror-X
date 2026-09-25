"""Pydantic schemas for AI Core, Behavioral Intelligence, and Model Registry."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetGenerateRequest(BaseModel):
    """Configuration for generating or compiling a behavioral training dataset."""

    num_examples: int = Field(
        100, ge=10, le=2000, description="Total number of structured examples to synthesize/extract"
    )
    seed: int = Field(42, description="Random seed for reproducible generation")
    include_existing_runs: bool = Field(True, description="Extract and label existing AgentRun database records")
    include_existing_scenarios: bool = Field(
        True, description="Extract and transform existing ScenarioRecord database records"
    )
    name: str = Field("behavior-dataset-v1", description="Identifier name for this generated dataset")


class BehaviorExample(BaseModel):
    """A single structured training example with explainable provenance."""

    example_id: str
    source_type: str  # agent_run, scenario_trace, synthetic_generator
    source_reference: str
    scenario_features: dict[str, Any]
    agent_version: str
    model_reference: str
    action_sequence: list[str]
    tool_usage: dict[str, int]
    policy_decisions: dict[str, int]
    execution_outcome: str  # completed, failed
    timing_features: dict[str, float]
    error_features: dict[str, Any]
    behavioral_label: str  # successful, failed, policy_violation, incorrect_tool, unnecessary_action, unexpected_action, abnormal_sequence
    label_provenance: str


class DatasetSummaryResponse(BaseModel):
    """Summary of compiled behavioral dataset."""

    dataset_id: str | None = None
    name: str
    total_examples: int
    seed: int
    classes_distribution: dict[str, int]
    sources_distribution: dict[str, int]
    provenance_notes: list[str]


class ExperimentRunRequest(BaseModel):
    """Configuration to launch a reproducible model training experiment."""

    name: str = Field(..., description="Experiment run name")
    model_type: str = Field("baseline_logistic", description="'baseline_logistic' or 'deep_sequence_gru'")
    model_version: str = Field("1.0.0", description="Semver identifier for model")
    feature_version: str = Field("v1.0", description="Feature engineering version")
    seed: int = Field(42, description="Random seed for reproducible weights and splits")
    test_split: float = Field(0.2, ge=0.05, le=0.5, description="Holdout test split ratio")
    val_split: float = Field(0.15, ge=0.05, le=0.4, description="Validation split ratio")
    hyperparameters: dict[str, Any] = Field(
        default_factory=lambda: {
            "learning_rate": 0.05,
            "epochs": 100,
            "l2_reg": 0.001,
            "embedding_dim": 16,
            "hidden_dim": 32,
        },
        description="Training hyperparameters",
    )
    dataset_name: str = Field("behavior-dataset-v1", description="Dataset identifier to train on")


class ExperimentResponse(BaseModel):
    """Detailed experiment execution results."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    model_type: str
    model_version: str
    feature_version: str
    seed: int
    dataset_config: dict[str, Any]
    hyperparameters: dict[str, Any]
    metrics: dict[str, Any]
    training_duration_ms: float
    artifact_path: str | None = None
    created_at: datetime


class ModelRegistryResponse(BaseModel):
    """Model registry metadata item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    model_type: str
    feature_version: str
    experiment_id: uuid.UUID
    status: str  # candidate, champion, archived
    metrics_summary: dict[str, Any]
    artifact_path: str | None = None
    created_at: datetime


class ModelPromoteRequest(BaseModel):
    """Request to promote or archive a registered model."""

    target_status: str = Field("champion", description="'champion', 'candidate', or 'archived'")


class BehavioralFinding(BaseModel):
    """Distinct classification of a behavioral observation."""

    category: str  # deterministic_policy_violation, model_based_anomaly, heuristic_warning, uncertain_prediction
    title: str
    description: str
    confidence: float
    evidence_reference: str | None = None
    is_hard_fact: bool = False


class AnalyzeRunResponse(BaseModel):
    """Comprehensive behavioral analysis of an AgentRun."""

    run_id: str
    agent_id: str
    trace_id: str
    deterministic_policy_violations: list[BehavioralFinding]
    model_based_anomalies: list[BehavioralFinding]
    heuristic_warnings: list[BehavioralFinding]
    uncertain_predictions: list[BehavioralFinding]
    feature_vector_summary: dict[str, float]
    predicted_behavior_label: str
    prediction_confidence: float
    evidence_id: str | None = None
    explanation: str


class PredictRequest(BaseModel):
    """Inference request for custom features or tool sequences."""

    features: dict[str, float] | None = None
    action_sequence: list[str] | None = None
    model_type: str | None = Field(None, description="baseline_logistic or deep_sequence_gru")


class PredictResponse(BaseModel):
    """Model prediction result with honest uncertainty disclosure."""

    predicted_label: str
    confidence: float
    probabilities: dict[str, float]
    is_anomaly: bool
    model_name: str
    model_version: str
    model_type: str
    classification_nature: str  # 'probabilistic_model_prediction' - never presented as absolute truth
    uncertainty_note: str | None = None
