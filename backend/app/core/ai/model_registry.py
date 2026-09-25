"""Model Registry for Behavioral Intelligence.

Tracks candidate, champion, and archived models, manages promotion lifecycles,
and loads serialized model artifacts for production inference.
"""

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.baseline_model import BaselineLogisticClassifier
from app.core.ai.features import BehavioralFeatureExtractor
from app.core.ai.sequence_model import SequenceGRUClassifier
from app.models.ai import AIModelRegistry


class ModelRegistryManager:
    """Manages model registry records and model instantiation."""

    async def list_models(self, db: AsyncSession) -> list[AIModelRegistry]:
        """Retrieve all registered models ordered by creation date."""
        query = select(AIModelRegistry).order_by(AIModelRegistry.created_at.desc())
        res = await db.execute(query)
        return list(res.scalars().all())

    async def get_model_by_id(self, db: AsyncSession, model_id: uuid.UUID) -> AIModelRegistry | None:
        """Find a model record by primary key."""
        query = select(AIModelRegistry).where(AIModelRegistry.id == model_id)
        res = await db.execute(query)
        return res.scalar_one_or_none()

    async def get_champion_model(self, db: AsyncSession, model_type: str | None = None) -> AIModelRegistry | None:
        """Retrieve current champion model (optionally filtered by type)."""
        query = select(AIModelRegistry).where(AIModelRegistry.status == "champion")
        if model_type:
            query = query.where(AIModelRegistry.model_type == model_type)
        query = query.order_by(AIModelRegistry.created_at.desc())
        res = await db.execute(query)
        champion = res.scalar_one_or_none()

        # Fallback to latest candidate if no champion set yet
        if not champion:
            fallback_query = select(AIModelRegistry)
            if model_type:
                fallback_query = fallback_query.where(AIModelRegistry.model_type == model_type)
            fallback_query = fallback_query.order_by(AIModelRegistry.created_at.desc())
            f_res = await db.execute(fallback_query)
            champion = f_res.scalar_one_or_none()

        return champion

    async def promote_model(
        self,
        db: AsyncSession,
        model_id: uuid.UUID,
        target_status: str = "champion",
    ) -> AIModelRegistry:
        """Promote model to champion or archive it. Demotes previous champions of same model_type."""
        model = await self.get_model_by_id(db, model_id)
        if not model:
            raise ValueError(f"Model '{model_id}' not found in registry")

        if target_status == "champion":
            # Demote existing champions of the same type to candidate
            query = select(AIModelRegistry).where(
                AIModelRegistry.model_type == model.model_type,
                AIModelRegistry.status == "champion",
                AIModelRegistry.id != model_id,
            )
            res = await db.execute(query)
            for existing in res.scalars().all():
                existing.status = "candidate"

        model.status = target_status
        await db.flush()
        return model

    def load_model_instance(self, model_record: AIModelRegistry) -> tuple[Any, Any]:
        """Load and instantiate model and feature processor from serialized artifact."""
        if not model_record.artifact_path or not Path(model_record.artifact_path).exists():
            raise FileNotFoundError(f"Model artifact not found at {model_record.artifact_path}")

        raw_data = json.loads(Path(model_record.artifact_path).read_text(encoding="utf-8"))
        model_type = raw_data.get("model_type")

        if model_type == "baseline_logistic":
            model = BaselineLogisticClassifier.from_dict(raw_data)
            extractor = BehavioralFeatureExtractor()
            extractor.feature_means = raw_data.get("scaler_means", {})
            extractor.feature_stds = raw_data.get("scaler_stds", {})
            return model, extractor

        elif model_type == "deep_sequence_gru":
            model = SequenceGRUClassifier.from_dict(raw_data)
            extractor = BehavioralFeatureExtractor()
            extractor.vocab = raw_data.get("vocab", extractor.vocab)
            return model, extractor

        else:
            raise ValueError(f"Unsupported model type in artifact: {model_type}")
