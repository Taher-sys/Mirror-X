"""Agent Behavior Lab Evaluator.

Extracts behavioral features from AgentRun execution traces, runs baseline and sequence
intelligence models, distinguishes deterministic violations from probabilistic anomalies,
and connects results to the Evidence Ledger.
"""

from collections import Counter
import hashlib
import json
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ai.features import BehavioralFeatureExtractor
from app.core.ai.model_registry import ModelRegistryManager
from app.models.agent import AgentRun
from app.models.evidence import EvidenceRecord
from app.models.trust import PolicyDecision
from app.schemas.ai import AnalyzeRunResponse, BehavioralFinding


class AgentLabEvaluator:
    """Evaluates AgentRun telemetry against deterministic rules and probabilistic models."""

    def __init__(self) -> None:
        self.registry = ModelRegistryManager()
        self.extractor = BehavioralFeatureExtractor()

    async def evaluate_run(
        self,
        db: AsyncSession,
        run_id: uuid.UUID,
        create_evidence: bool = True,
    ) -> AnalyzeRunResponse:
        """Analyze an AgentRun, distinguishing deterministic violations from probabilistic predictions."""
        # 1. Fetch AgentRun with steps
        stmt = select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == run_id)
        res = await db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            raise ValueError(f"AgentRun '{run_id}' not found")

        steps = list(run.steps) if run.steps else []

        # 2. Fetch associated PolicyDecisions
        dec_stmt = select(PolicyDecision).order_by(PolicyDecision.created_at.desc()).limit(100)
        dec_res = await db.execute(dec_stmt)
        all_decisions = list(dec_res.scalars().all())
        decisions = [
            d for d in all_decisions
            if (d.agent_name and (d.agent_name == str(run.agent_id) or d.agent_name in (run.agent_version, run.goal)))
            or (isinstance(d.context_snapshot, dict) and d.context_snapshot.get("trace_id") == run.trace_id)
        ]

        # Collections for distinct categories
        deterministic_violations: list[BehavioralFinding] = []
        model_anomalies: list[BehavioralFinding] = []
        heuristic_warnings: list[BehavioralFinding] = []
        uncertain_predictions: list[BehavioralFinding] = []

        # 3. Check Deterministic Policy Violations (Hard Facts)
        pol_violations = getattr(run, "policy_violations_count", 0)
        if pol_violations > 0:
            deterministic_violations.append(
                BehavioralFinding(
                    category="deterministic_policy_violation",
                    title="Policy Violation Counter Exceeded",
                    description=f"Agent logged {pol_violations} explicit policy violation events during task execution.",
                    confidence=1.0,
                    evidence_reference=f"agent_runs/{run.id}:policy_violations_count={pol_violations}",
                    is_hard_fact=True,
                )
            )

        for d in decisions:
            if d.result == "DENY":
                act_name = getattr(d, "action_name", "action")
                res_name = getattr(d, "resource_name", "resource")
                deterministic_violations.append(
                    BehavioralFinding(
                        category="deterministic_policy_violation",
                        title=f"Trust Layer Policy DENY on Action '{act_name}'",
                        description=f"Policy decision {d.id} explicitly denied action '{act_name}' on resource '{res_name}': {d.reason}",
                        confidence=1.0,
                        evidence_reference=f"policy_decisions/{d.id}",
                        is_hard_fact=True,
                    )
                )

        for s in steps:
            pol_failed = (getattr(s, "status", "") == "policy_denied") or (
                isinstance(getattr(s, "policy_check", None), dict) and not s.policy_check.get("allowed", True)
            )
            if pol_failed:
                deterministic_violations.append(
                    BehavioralFinding(
                        category="deterministic_policy_violation",
                        title=f"Step {s.step_number} Policy Gate Failed",
                        description=f"Step attempted tool call '{s.tool_call}' which failed automated policy gate validation.",
                        confidence=1.0,
                        evidence_reference=f"agent_steps/{s.id}",
                        is_hard_fact=True,
                    )
                )

        # 4. Check Heuristic Warnings (Rules)
        action_seq = [
            getattr(s, "tool_name", None) or (s.tool_call if hasattr(s, "tool_call") else "unknown")
            for s in steps
            if s
        ]

        # Redundant reads
        counts = Counter(action_seq)
        for act, count in counts.items():
            if act in ("read_file", "query_database") and count >= 3:
                heuristic_warnings.append(
                    BehavioralFinding(
                        category="heuristic_warning",
                        title=f"Potential Idempotent Loop: '{act}'",
                        description=f"Agent invoked idempotent read operation '{act}' {count} times within a single execution trace.",
                        confidence=0.85,
                        evidence_reference=f"trace_entropy={self.extractor.compute_entropy(action_seq)}",
                        is_hard_fact=False,
                    )
                )

        # High step duration
        for s in steps:
            duration = getattr(s, "duration_ms", 0.0) or getattr(s, "execution_duration_ms", 0.0)
            if duration > 5000.0:
                heuristic_warnings.append(
                    BehavioralFinding(
                        category="heuristic_warning",
                        title=f"Step {s.step_number} Execution Latency Spike",
                        description=f"Tool '{s.tool_call}' took {duration:.1f}ms to execute (threshold: 5000ms).",
                        confidence=0.90,
                        evidence_reference=f"agent_steps/{s.id}:duration_ms={duration}",
                        is_hard_fact=False,
                    )
                )

        # 5. Extract Feature Vector and Run ML Models
        example_dict = {
            "action_sequence": action_seq,
            "tool_usage": dict(counts),
            "policy_decisions": {
                "ALLOW": sum(1 for d in decisions if d.result == "ALLOW"),
                "DENY": sum(1 for d in decisions if d.result == "DENY"),
                "HUMAN_REVIEW_REQUIRED": sum(1 for d in decisions if d.result == "HUMAN_REVIEW_REQUIRED"),
            },
            "timing_features": {
                "latency_ms": float(run.latency_ms or 120.0),
                "avg_step_duration_ms": float(run.latency_ms or 120.0) / max(1, len(action_seq)),
            },
            "error_features": {
                "error_count": run.error_count,
                "has_error": run.error_count > 0,
            },
            "scenario_features": {
                "scenario_class": "normal",
                "has_constraints": False,
            },
            "execution_outcome": "completed" if run.successful_completion else "failed",
            "behavioral_label": "successful",
        }

        raw_features = self.extractor.extract_raw_features(example_dict)
        pred_label = "successful"
        pred_conf = 0.95

        # Attempt to run registered champion baseline model
        champion = await self.registry.get_champion_model(db)
        if champion:
            try:
                model, feat_proc = self.registry.load_model_instance(champion)
                if champion.model_type == "baseline_logistic":
                    x_norm = feat_proc.transform_features(raw_features)
                    pred_label, pred_conf, probs = model.predict(x_norm)
                elif champion.model_type == "deep_sequence_gru":
                    tokens = feat_proc.tokenize_sequence(action_seq)
                    pred_label, pred_conf, probs = model.predict(tokens)

                # Check for statistical anomaly prediction
                if pred_label not in ("successful",) and pred_conf >= 0.60:
                    model_anomalies.append(
                        BehavioralFinding(
                            category="model_based_anomaly",
                            title=f"Model Classified Behavior as '{pred_label}'",
                            description=(
                                f"Champion model '{champion.name}:{champion.version}' inferred behavior state "
                                f"'{pred_label}' with {pred_conf*100:.1f}% confidence. Note: This is an empirical "
                                f"statistical prediction and not an absolute ground truth."
                            ),
                            confidence=pred_conf,
                            evidence_reference=f"model_registry/{champion.id}",
                            is_hard_fact=False,
                        )
                    )

                # Check for uncertain prediction
                sorted_probs = sorted(probs.values(), reverse=True)
                if pred_conf < 0.60 or (len(sorted_probs) > 1 and (sorted_probs[0] - sorted_probs[1]) < 0.15):
                    uncertain_predictions.append(
                        BehavioralFinding(
                            category="uncertain_prediction",
                            title="High Classification Ambiguity",
                            description=(
                                f"Model top confidence is {pred_conf*100:.1f}%. The distribution across behavioral "
                                f"classes exhibits high entropy, indicating the execution pattern does not match canonical clusters."
                            ),
                            confidence=pred_conf,
                            evidence_reference=f"model_entropy_distribution:{probs}",
                            is_hard_fact=False,
                        )
                    )

            except Exception as e:
                heuristic_warnings.append(
                    BehavioralFinding(
                        category="heuristic_warning",
                        title="Model Inference Fallback",
                        description=f"Champion model inference encountered error: {str(e)}. Defaulting to deterministic rule analysis.",
                        confidence=0.5,
                        is_hard_fact=False,
                    )
                )

        # 6. Connect results to Evidence Ledger
        evidence_id = None
        if create_evidence:
            evidence_summary = (
                f"Behavioral evaluation for AgentRun {run.id}: "
                f"{len(deterministic_violations)} deterministic violations, "
                f"{len(model_anomalies)} model anomalies, "
                f"{len(heuristic_warnings)} heuristic warnings. "
                f"Predicted state: {pred_label} ({pred_conf*100:.1f}% confidence)."
            )
            raw_payload = {
                "run_id": str(run.id),
                "agent_id": str(run.agent_id),
                "trace_id": run.trace_id,
                "deterministic_violations": [v.model_dump() for v in deterministic_violations],
                "model_anomalies": [m.model_dump() for m in model_anomalies],
                "heuristic_warnings": [h.model_dump() for h in heuristic_warnings],
                "uncertain_predictions": [u.model_dump() for u in uncertain_predictions],
                "predicted_label": pred_label,
                "prediction_confidence": pred_conf,
            }
            content_str = json.dumps(raw_payload, sort_keys=True)
            sha = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

            evidence_rec = EvidenceRecord(
                evidence_type="behavioral_analysis",
                source_reference=f"agent_runs/{run.id}",
                summary=evidence_summary,
                raw_payload=raw_payload,
                confidence=1.0 if not uncertain_predictions else 0.75,
                hash_signature=sha,
            )
            db.add(evidence_rec)
            await db.flush()
            evidence_id = str(evidence_rec.id)

        explanation = (
            f"Analysis complete. Findings separated into {len(deterministic_violations)} deterministic policy violations (facts), "
            f"{len(model_anomalies)} model-based anomalies (probabilistic), and {len(heuristic_warnings)} operational warnings."
        )

        return AnalyzeRunResponse(
            run_id=str(run.id),
            agent_id=str(run.agent_id),
            trace_id=run.trace_id or "",
            deterministic_policy_violations=deterministic_violations,
            model_based_anomalies=model_anomalies,
            heuristic_warnings=heuristic_warnings,
            uncertain_predictions=uncertain_predictions,
            feature_vector_summary={k: round(v, 2) for k, v in list(raw_features.items())[:8]},
            predicted_behavior_label=pred_label,
            prediction_confidence=pred_conf,
            evidence_id=evidence_id,
            explanation=explanation,
        )
