"""Agent version behavioral comparison engine.

Compares measurable behaviors across agent versions or runs without collapsing
into an arbitrary 'intelligence score'.
"""

from typing import Any


class AgentVersionComparator:
    """Calculates multidimensional behavioral deltas across agent versions."""

    @staticmethod
    def compare_runs(baseline_run: dict[str, Any], candidate_run: dict[str, Any]) -> dict[str, Any]:
        """Compare two specific runs across all eight mandatory measurable behaviors."""
        b_metrics = baseline_run.get("metrics", baseline_run)
        c_metrics = candidate_run.get("metrics", candidate_run)

        # Baseline values
        b_complete = bool(b_metrics.get("successful_completion", False))
        c_complete = bool(c_metrics.get("successful_completion", False))

        b_correct = int(b_metrics.get("correct_tool_selection_count", 0))
        c_correct = int(c_metrics.get("correct_tool_selection_count", 0))

        b_incorrect = int(b_metrics.get("incorrect_tool_use_count", 0))
        c_incorrect = int(c_metrics.get("incorrect_tool_use_count", 0))

        b_unnecessary = int(b_metrics.get("unnecessary_actions_count", 0))
        c_unnecessary = int(c_metrics.get("unnecessary_actions_count", 0))

        b_violations = int(b_metrics.get("policy_violations_count", 0))
        c_violations = int(c_metrics.get("policy_violations_count", 0))

        b_errors = int(b_metrics.get("error_count", 0))
        c_errors = int(c_metrics.get("error_count", 0))

        b_latency = float(b_metrics.get("latency_ms", 0.0))
        c_latency = float(c_metrics.get("latency_ms", 0.0))

        b_retries = int(b_metrics.get("retry_count", 0))
        c_retries = int(c_metrics.get("retry_count", 0))

        deltas = {
            "successful_completion": {
                "baseline": b_complete,
                "candidate": c_complete,
                "improved": (c_complete and not b_complete),
                "regressed": (b_complete and not c_complete),
            },
            "correct_tool_selection": {
                "baseline": b_correct,
                "candidate": c_correct,
                "delta": c_correct - b_correct,
                "improved": c_correct >= b_correct,
            },
            "incorrect_tool_use": {
                "baseline": b_incorrect,
                "candidate": c_incorrect,
                "delta": c_incorrect - b_incorrect,
                "improved": c_incorrect <= b_incorrect,
            },
            "unnecessary_actions": {
                "baseline": b_unnecessary,
                "candidate": c_unnecessary,
                "delta": c_unnecessary - b_unnecessary,
                "improved": c_unnecessary <= b_unnecessary,
            },
            "policy_violations": {
                "baseline": b_violations,
                "candidate": c_violations,
                "delta": c_violations - b_violations,
                "improved": c_violations <= b_violations,
            },
            "error_count": {
                "baseline": b_errors,
                "candidate": c_errors,
                "delta": c_errors - b_errors,
                "improved": c_errors <= b_errors,
            },
            "latency_ms": {
                "baseline": b_latency,
                "candidate": c_latency,
                "delta": round(c_latency - b_latency, 2),
                "improved": c_latency <= b_latency,
            },
            "retry_count": {
                "baseline": b_retries,
                "candidate": c_retries,
                "delta": c_retries - b_retries,
                "improved": c_retries <= b_retries,
            },
        }

        return {
            "baseline_version": baseline_run.get("agent_version", "baseline"),
            "candidate_version": candidate_run.get("agent_version", "candidate"),
            "baseline_trace_id": baseline_run.get("trace_id"),
            "candidate_trace_id": candidate_run.get("trace_id"),
            "behavioral_matrix": deltas,
            "disclaimer": "MIRROR-X does not compute an arbitrary single 'intelligence score'. All metrics are observable, measurable behaviors.",
        }
