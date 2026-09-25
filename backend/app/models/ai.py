"""SQLAlchemy models for AI Core, Behavioral Intelligence, and Model Registry."""

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel


class AIExperiment(BaseModel):
    """Tracks training runs, hyperparameters, dataset configuration, and evaluation metrics."""

    __tablename__ = "ai_experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)  # baseline_logistic, deep_sequence_gru
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)

    # Configuration payloads
    dataset_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Metrics results
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    training_duration_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Serialized model artifact reference
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    registered_models: Mapped[list["AIModelRegistry"]] = relationship(
        "AIModelRegistry",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class AIModelRegistry(BaseModel):
    """Model registry tracking operational status (candidate, champion, archived) and lineage."""

    __tablename__ = "ai_model_registry"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False)

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("ai_experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="candidate"
    )  # candidate, champion, archived
    metrics_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    experiment: Mapped["AIExperiment"] = relationship("AIExperiment", back_populates="registered_models")


class BehaviorDatasetRecord(BaseModel):
    """Metadata record of generated training/evaluation datasets with provenance."""

    __tablename__ = "behavior_datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    num_examples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    classes_distribution: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    provenance_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
