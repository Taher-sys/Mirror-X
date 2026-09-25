"""Behavior Dataset Generator.

Transforms AgentRun, AgentStep, Scenario, and PolicyDecision records into
structured, labeled training examples with complete explainable provenance.
Does NOT download or depend on external ML datasets.
"""

import random
import uuid
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import AgentRun
from app.models.scenario import ScenarioRecord
from app.models.trust import PolicyDecision

BEHAVIOR_LABELS = [
    "successful",
    "failed",
    "policy_violation",
    "incorrect_tool",
    "unnecessary_action",
    "unexpected_action",
    "abnormal_sequence",
]

AVAILABLE_SANDBOX_TOOLS = [
    "query_database",
    "read_file",
    "write_file",
    "http_request",
    "parse_ast",
    "check_policy",
    "run_sandbox_test",
    "diff_analyzer",
    "export_metrics",
    "notify_reviewer",
]

UNAUTHORIZED_OR_DANGEROUS_ACTIONS = [
    "drop_production_table",
    "exec_raw_shell",
    "bypass_auth",
    "delete_cluster",
    "export_secret_keys",
    "force_push_main",
]


class BehaviorDatasetGenerator:
    """Pipeline for generating and compiling behavioral training datasets."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def label_agent_run(self, run: AgentRun, steps: list[Any], decisions: list[PolicyDecision]) -> tuple[str, str]:
        """Deterministically assign a behavioral label and explain its evidence-based provenance."""
        # 1. Check for explicit policy violations / denials
        has_deny_decision = any(d.result == "DENY" for d in decisions)
        step_policy_failed = any(
            (getattr(s, "status", "") == "policy_denied")
            or (isinstance(getattr(s, "policy_check", None), dict) and not s.policy_check.get("allowed", True))
            for s in steps
        )
        pol_violations = getattr(run, "policy_violations_count", 0)
        if pol_violations > 0 or has_deny_decision or step_policy_failed:
            reasons = []
            if pol_violations > 0:
                reasons.append(f"run.policy_violations_count={pol_violations}")
            if has_deny_decision:
                reasons.append("recorded PolicyDecision DENY")
            if step_policy_failed:
                reasons.append("step policy check failed")
            return "policy_violation", f"Deterministic policy violation: {', '.join(reasons)}"

        # 2. Check for incorrect tools
        incorrect_tools = getattr(run, "incorrect_tool_use_count", 0)
        if incorrect_tools > 0:
            return (
                "incorrect_tool",
                f"Deterministic incorrect tool usage: {incorrect_tools} invalid tool invocations recorded",
            )
        for step in steps:
            tool_name = getattr(step, "tool_name", None) or (step.tool_call if hasattr(step, "tool_call") else None)
            if tool_name and tool_name not in AVAILABLE_SANDBOX_TOOLS:
                return (
                    "incorrect_tool",
                    f"Undeclared tool invoked: '{tool_name}' not in registered sandbox tool registry",
                )

        # 3. Check for abnormal cyclic sequence (e.g. A -> B -> A -> B -> A -> B)
        action_seq = [
            getattr(step, "tool_name", None) or (step.tool_call if hasattr(step, "tool_call") else "no_op")
            for step in steps
            if step
        ]
        if len(action_seq) >= 6:
            # Check for 2-step oscillation
            if all(action_seq[i] == action_seq[i - 2] for i in range(2, len(action_seq))):
                return (
                    "abnormal_sequence",
                    f"Oscillating 2-step infinite loop detected: {' -> '.join(action_seq[:4])}...",
                )

        # 4. Check for unnecessary / redundant duplicate actions
        unnecessary_acts = getattr(run, "unnecessary_actions_count", 0)
        if unnecessary_acts > 0:
            return "unnecessary_action", f"Run flagged {unnecessary_acts} unnecessary or redundant actions"
        if len(action_seq) >= 3 and len(set(action_seq)) == 1 and action_seq[0] in ("read_file", "query_database"):
            return (
                "unnecessary_action",
                f"Redundant repeated idempotent reads of identical tool: {action_seq[0]} x{len(action_seq)}",
            )

        # 5. Check for runtime errors or hard failures
        if run.error_count > 0 or run.status == "failed":
            error_reasons = []
            if run.error_count > 0:
                error_reasons.append(f"error_count={run.error_count}")
            if run.status == "failed":
                error_reasons.append("status='failed'")
            return "failed", f"Operational runtime execution failure: {', '.join(error_reasons)}"

        # 6. Check for unexpected actions (e.g. destructive action attempted when goal is read-only)
        goal_lower = (run.goal or "").lower()
        if any(kw in goal_lower for kw in ("read", "view", "inspect", "list", "check")):
            if any(act in ("write_file", "run_sandbox_test") for act in action_seq):
                return (
                    "unexpected_action",
                    f"Unexpected state-modifying action for read-only inspection goal '{run.goal}'",
                )

        # 7. Otherwise, successful execution
        return "successful", "Execution completed all steps without errors, policy violations, or anomalous loops"

    def synthesize_example(self, target_label: str, index: int) -> dict[str, Any]:
        """Synthesize a reproducible behavioral trace for a target label."""
        example_id = str(uuid.UUID(int=self.rng.getrandbits(128), version=4))
        agent_versions = ["v1.0.0", "v1.1.0-preview", "v2.0.0-rc1"]
        model_refs = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "llama-3.1-70b"]
        scenario_classes = ["normal", "boundary", "incomplete", "malformed", "unauthorized", "adversarial", "outage"]

        agent_version = self.rng.choice(agent_versions)
        model_ref = self.rng.choice(model_refs)
        scenario_class = self.rng.choice(scenario_classes)

        action_sequence: list[str] = []
        tool_usage: dict[str, int] = {}
        policy_decisions = {"ALLOW": 0, "DENY": 0, "HUMAN_REVIEW_REQUIRED": 0}
        error_features = {"error_count": 0, "has_error": False, "error_messages": []}
        timing_features: dict[str, float] = {}

        if target_label == "successful":
            scenario_class = "normal"
            seq_len = self.rng.randint(2, 5)
            action_sequence = [
                self.rng.choice(["query_database", "read_file", "parse_ast", "diff_analyzer", "check_policy"])
                for _ in range(seq_len)
            ]
            policy_decisions["ALLOW"] = len(action_sequence)
            exec_outcome = "completed"
            latency = float(self.rng.randint(80, 450))
            provenance = "Synthesized standard compliant execution trace meeting all scenario constraints"

        elif target_label == "failed":
            scenario_class = self.rng.choice(["outage", "malformed", "boundary"])
            seq_len = self.rng.randint(2, 4)
            action_sequence = [
                self.rng.choice(["query_database", "http_request", "run_sandbox_test"]) for _ in range(seq_len)
            ]
            policy_decisions["ALLOW"] = len(action_sequence)
            error_count = self.rng.randint(1, 3)
            error_features["error_count"] = error_count
            error_features["has_error"] = True
            error_features["error_messages"] = [f"Downstream service connection reset on step {seq_len}"]
            exec_outcome = "failed"
            latency = float(self.rng.randint(300, 1500))
            provenance = (
                f"Synthesized trace simulating external dependency failure and unhandled exceptions ({scenario_class})"
            )

        elif target_label == "policy_violation":
            scenario_class = "unauthorized"
            action_sequence = ["query_database", "read_file", self.rng.choice(UNAUTHORIZED_OR_DANGEROUS_ACTIONS)]
            policy_decisions["ALLOW"] = 2
            policy_decisions["DENY"] = 1
            exec_outcome = "failed"
            latency = float(self.rng.randint(100, 400))
            provenance = "Synthesized trace invoking dangerous action intercepted by Trust Layer Policy DENY"

        elif target_label == "incorrect_tool":
            scenario_class = "malformed"
            invalid_tool = self.rng.choice(
                ["undefined_executor", "eval_bash_code", "call_unregistered_rpc", "system_probe"]
            )
            action_sequence = ["query_database", invalid_tool]
            policy_decisions["ALLOW"] = 1
            error_features["error_count"] = 1
            error_features["has_error"] = True
            error_features["error_messages"] = [f"Tool '{invalid_tool}' not registered in environment schema"]
            exec_outcome = "failed"
            latency = float(self.rng.randint(50, 250))
            provenance = f"Synthesized trace attempting invocation of unregistered tool '{invalid_tool}'"

        elif target_label == "unnecessary_action":
            scenario_class = "normal"
            repeated_tool = self.rng.choice(["read_file", "query_database"])
            action_sequence = [repeated_tool, repeated_tool, repeated_tool, repeated_tool]
            policy_decisions["ALLOW"] = 4
            exec_outcome = "completed"
            latency = float(self.rng.randint(200, 600))
            provenance = f"Synthesized trace with redundant identical idempotent reads ({repeated_tool} x4)"

        elif target_label == "unexpected_action":
            scenario_class = "boundary"
            action_sequence = ["read_file", "export_metrics", "write_file"]
            policy_decisions["ALLOW"] = 2
            policy_decisions["HUMAN_REVIEW_REQUIRED"] = 1
            exec_outcome = "completed"
            latency = float(self.rng.randint(150, 500))
            provenance = "Synthesized trace performing unexpected file modification during diagnostic read workflow"

        elif target_label == "abnormal_sequence":
            scenario_class = "adversarial"
            action_sequence = [
                "query_database",
                "http_request",
                "query_database",
                "http_request",
                "query_database",
                "http_request",
            ]
            policy_decisions["ALLOW"] = 6
            exec_outcome = "failed"
            latency = float(self.rng.randint(400, 1200))
            provenance = "Synthesized trace exhibiting pathological 2-step infinite cyclic oscillation"
        else:
            action_sequence = ["query_database", "read_file"]
            exec_outcome = "completed"
            latency = 100.0
            provenance = "Fallback example"

        tool_usage = dict(Counter(action_sequence))
        avg_step = latency / max(1, len(action_sequence))
        timing_features = {
            "latency_ms": round(latency, 2),
            "avg_step_duration_ms": round(avg_step, 2),
            "max_step_duration_ms": round(avg_step * 1.5, 2),
        }

        return {
            "example_id": example_id,
            "source_type": "synthetic_generator",
            "source_reference": f"synthetic://seed-{self.seed}/scenario-{scenario_class}/ex-{index}",
            "scenario_features": {
                "scenario_class": scenario_class,
                "has_constraints": scenario_class != "normal",
                "is_adversarial": scenario_class in ("adversarial", "unauthorized"),
                "resource_count": len(set(action_sequence)),
            },
            "agent_version": agent_version,
            "model_reference": model_ref,
            "action_sequence": action_sequence,
            "tool_usage": tool_usage,
            "policy_decisions": policy_decisions,
            "execution_outcome": exec_outcome,
            "timing_features": timing_features,
            "error_features": error_features,
            "behavioral_label": target_label,
            "label_provenance": provenance,
        }

    async def extract_from_db(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Extract and label existing AgentRun and PolicyDecision records from MySQL."""
        examples: list[dict[str, Any]] = []

        stmt = select(AgentRun).options(selectinload(AgentRun.steps)).order_by(AgentRun.created_at.desc())
        runs_res = await db.execute(stmt)
        runs = runs_res.scalars().all()

        decisions_res = await db.execute(select(PolicyDecision).order_by(PolicyDecision.created_at.desc()))
        decisions = decisions_res.scalars().all()

        scenarios_res = await db.execute(select(ScenarioRecord).order_by(ScenarioRecord.created_at.desc()))
        scenarios = {str(s.id): s for s in scenarios_res.scalars().all()}

        for run in runs:
            run_steps = list(run.steps) if run.steps else []
            run_decisions = [d for d in decisions if str(d.id) in (run.trace_id or "")]

            label, provenance = self.label_agent_run(run, run_steps, run_decisions)

            action_seq = [
                getattr(s, "tool_name", None) or (s.tool_call if hasattr(s, "tool_call") else "action")
                for s in run_steps
                if s
            ]
            if not action_seq:
                action_seq = ["start_session", "complete_session"]

            tool_counts = dict(Counter(action_seq))
            policy_summary = {
                "ALLOW": sum(1 for d in run_decisions if d.result == "ALLOW"),
                "DENY": sum(1 for d in run_decisions if d.result == "DENY"),
                "HUMAN_REVIEW_REQUIRED": sum(1 for d in run_decisions if d.result == "HUMAN_REVIEW_REQUIRED"),
            }

            sc_class = "normal"
            if isinstance(run.context_reference, dict):
                sc_id = str(run.context_reference.get("scenario_id") or run.context_reference.get("id") or "")
                if sc_id in scenarios:
                    sc_class = scenarios[sc_id].scenario_class
                elif "scenario_class" in run.context_reference:
                    sc_class = str(run.context_reference["scenario_class"])
            elif isinstance(run.context_reference, str) and run.context_reference in scenarios:
                sc_class = scenarios[run.context_reference].scenario_class

            latency = float(run.latency_ms or 120.0)
            avg_duration = latency / max(1, len(action_seq))

            examples.append(
                {
                    "example_id": str(run.id),
                    "source_type": "agent_run",
                    "source_reference": f"db://agent_runs/{run.id} (trace:{run.trace_id})",
                    "scenario_features": {
                        "scenario_class": sc_class,
                        "has_constraints": sc_class != "normal",
                        "is_adversarial": sc_class in ("adversarial", "unauthorized"),
                        "resource_count": len(tool_counts),
                    },
                    "agent_version": f"agent_{run.agent_id}",
                    "model_reference": "standard_execution",
                    "action_sequence": action_seq,
                    "tool_usage": tool_counts,
                    "policy_decisions": policy_summary,
                    "execution_outcome": "completed" if run.successful_completion else "failed",
                    "timing_features": {
                        "latency_ms": latency,
                        "avg_step_duration_ms": round(avg_duration, 2),
                        "max_step_duration_ms": round(avg_duration * 1.5, 2),
                    },
                    "error_features": {
                        "error_count": getattr(run, "error_count", 0),
                        "has_error": getattr(run, "error_count", 0) > 0,
                        "error_messages": [
                            str(s.error)
                            for s in run_steps
                            if getattr(s, "error", None) or getattr(s, "status", "") == "tool_error"
                        ],
                    },
                    "behavioral_label": label,
                    "label_provenance": provenance,
                }
            )

        return examples

    async def compile_dataset(
        self,
        db: AsyncSession,
        num_examples: int = 100,
        include_existing_runs: bool = True,
        include_existing_scenarios: bool = True,
    ) -> list[dict[str, Any]]:
        """Compile a complete behavioral dataset combining DB telemetry and reproducible synthetic examples."""
        dataset: list[dict[str, Any]] = []

        if include_existing_runs:
            db_examples = await self.extract_from_db(db)
            dataset.extend(db_examples)

        # Fill remaining examples using deterministic seeded synthesis across all 7 labels
        remaining = max(0, num_examples - len(dataset))
        for i in range(remaining):
            target_label = BEHAVIOR_LABELS[i % len(BEHAVIOR_LABELS)]
            synthetic_ex = self.synthesize_example(target_label, i)
            dataset.append(synthetic_ex)

        # Shuffle deterministically with seed
        self.rng.shuffle(dataset)
        return dataset
