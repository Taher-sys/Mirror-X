"""Feature Engineering and Tokenization for Behavioral Intelligence.

Extracts deterministic numeric feature vectors and sequence tokens from structured
behavioral examples. Every feature is explicitly documented with its empirical formula.
"""

import math
from collections import Counter
from typing import Any

# Documented feature dictionary with definitions
FEATURE_DEFINITIONS: dict[str, str] = {
    "tool_call_frequency": "Total integer count of tool invocations throughout the execution run.",
    "unique_tools_count": "Cardinality of distinct tool types invoked (measures operational diversity).",
    "action_sequence_length": "Total length of the discrete action sequence (step count).",
    "retry_count": "Count of consecutive repeated identical tool invocations representing retry attempts.",
    "latency_ms": "Total execution wall-clock time in milliseconds.",
    "avg_step_duration_ms": "Mean duration per execution step in milliseconds.",
    "error_count": "Number of execution steps that encountered an unhandled exception or error.",
    "has_error": "Binary flag (1.0 if error_count > 0, else 0.0).",
    "policy_denials": "Count of Trust Layer policy evaluations resulting in explicit DENY.",
    "human_review_events": "Count of Trust Layer policy evaluations requiring HUMAN_REVIEW_REQUIRED.",
    "policy_violations": "Total count of logged policy violation counters.",
    "unnecessary_actions_count": "Count of redundant or duplicate idempotent reads without state changes.",
    "incorrect_tool_uses_count": "Count of attempts to invoke non-existent or unregistered tools.",
    "sandbox_access_ratio": "Ratio of sandbox-confined operations relative to total operations.",
    "action_order_entropy": "Shannon entropy of tool transition sequences; quantifies behavioral randomness vs deterministic predictability.",
    "max_consecutive_repeats": "Maximum run-length of identical consecutive tool calls (detects infinite loops).",
    "scenario_class_normal": "Binary flag indicating whether the execution occurred within a standard compliant scenario.",
    "scenario_class_adversarial": "Binary flag indicating whether the execution was tested against adversarial/unauthorized constraints.",
    "scenario_class_boundary": "Binary flag indicating boundary, malformed, or incomplete edge conditions.",
    "scenario_has_constraints": "Binary flag indicating whether the scenario had active validation constraints.",
    "execution_outcome_success": "Binary flag (1.0 if final execution outcome was completed, 0.0 if failed).",
}

FEATURE_KEYS = list(FEATURE_DEFINITIONS.keys())


class BehavioralFeatureExtractor:
    """Extracts deterministic feature vectors and sequence tokens from behavioral examples."""

    def __init__(self, max_sequence_length: int = 12) -> None:
        self.max_sequence_length = max_sequence_length
        self.feature_keys = FEATURE_KEYS

        # Default vocabulary of known tools and actions
        self.vocab: dict[str, int] = {
            "<PAD>": 0,
            "<UNK>": 1,
            "query_database": 2,
            "read_file": 3,
            "write_file": 4,
            "http_request": 5,
            "parse_ast": 6,
            "check_policy": 7,
            "run_sandbox_test": 8,
            "diff_analyzer": 9,
            "export_metrics": 10,
            "notify_reviewer": 11,
            "drop_production_table": 12,
            "exec_raw_shell": 13,
            "bypass_auth": 14,
            "delete_cluster": 15,
            "export_secret_keys": 16,
            "force_push_main": 17,
        }
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}

        # Scaler parameters (mean and std per feature)
        self.feature_means: dict[str, float] = {}
        self.feature_stds: dict[str, float] = {}

    def build_vocab_from_examples(self, examples: list[dict[str, Any]]) -> None:
        """Expand vocabulary dynamically from observed actions in dataset."""
        for ex in examples:
            for action in ex.get("action_sequence", []):
                if action not in self.vocab:
                    self.vocab[action] = len(self.vocab)
        self.inverse_vocab = {idx: token for token, idx in self.vocab.items()}

    def compute_entropy(self, sequence: list[str]) -> float:
        """Compute Shannon entropy of action sequence: H = -sum(p * log2(p))."""
        if not sequence:
            return 0.0
        counts = Counter(sequence)
        total = len(sequence)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 4)

    def compute_max_consecutive_repeats(self, sequence: list[str]) -> int:
        """Calculate maximum consecutive occurrences of the exact same action."""
        if not sequence:
            return 0
        max_run = 1
        current_run = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        return max_run

    def extract_raw_features(self, example: dict[str, Any]) -> dict[str, float]:
        """Extract unnormalized raw numerical features from a structured example."""
        action_seq = example.get("action_sequence", [])
        tool_usage = example.get("tool_usage", {})
        policy_decisions = example.get("policy_decisions", {})
        timing = example.get("timing_features", {})
        errors = example.get("error_features", {})
        scenario = example.get("scenario_features", {})

        sc_class = scenario.get("scenario_class", "normal")
        deny_count = float(policy_decisions.get("DENY", 0))
        review_count = float(policy_decisions.get("HUMAN_REVIEW_REQUIRED", 0))
        error_count = float(errors.get("error_count", 0))
        seq_len = float(len(action_seq))
        unique_tools = float(len(tool_usage))

        # Check for retry count (consecutive repeats)
        max_repeats = self.compute_max_consecutive_repeats(action_seq)
        retries = float(max(0, max_repeats - 1))

        # Check sandbox ratio
        sandbox_actions = sum(
            1
            for act in action_seq
            if not any(kw in act for kw in ("production", "raw_shell", "bypass", "delete_cluster", "secret_keys"))
        )
        sandbox_ratio = sandbox_actions / max(1.0, seq_len)

        # Label indicators
        label = example.get("behavioral_label", "")
        incorrect_tools = 1.0 if label == "incorrect_tool" else 0.0
        unnecessary_actions = 1.0 if label == "unnecessary_action" else 0.0
        policy_violations = 1.0 if label == "policy_violation" or deny_count > 0 else 0.0

        raw: dict[str, float] = {
            "tool_call_frequency": float(sum(tool_usage.values())),
            "unique_tools_count": unique_tools,
            "action_sequence_length": seq_len,
            "retry_count": retries,
            "latency_ms": float(timing.get("latency_ms", 100.0)),
            "avg_step_duration_ms": float(timing.get("avg_step_duration_ms", 50.0)),
            "error_count": error_count,
            "has_error": 1.0 if error_count > 0 or errors.get("has_error") else 0.0,
            "policy_denials": deny_count,
            "human_review_events": review_count,
            "policy_violations": policy_violations,
            "unnecessary_actions_count": unnecessary_actions,
            "incorrect_tool_uses_count": incorrect_tools,
            "sandbox_access_ratio": sandbox_ratio,
            "action_order_entropy": self.compute_entropy(action_seq),
            "max_consecutive_repeats": float(max_repeats),
            "scenario_class_normal": 1.0 if sc_class == "normal" else 0.0,
            "scenario_class_adversarial": 1.0 if sc_class in ("adversarial", "unauthorized") else 0.0,
            "scenario_class_boundary": 1.0 if sc_class in ("boundary", "malformed", "outage") else 0.0,
            "scenario_has_constraints": 1.0 if scenario.get("has_constraints") else 0.0,
            "execution_outcome_success": 1.0 if example.get("execution_outcome") == "completed" else 0.0,
        }
        return raw

    def fit_scaler(self, raw_feature_dicts: list[dict[str, float]]) -> None:
        """Fit z-score normalization parameters (mean and std) on training set."""
        if not raw_feature_dicts:
            return
        n = len(raw_feature_dicts)
        for key in self.feature_keys:
            vals = [d.get(key, 0.0) for d in raw_feature_dicts]
            mean = sum(vals) / n
            variance = sum((x - mean) ** 2 for x in vals) / max(1, n - 1)
            std = math.sqrt(variance)
            self.feature_means[key] = mean
            self.feature_stds[key] = std if std > 1e-6 else 1.0

    def transform_features(self, raw_features: dict[str, float]) -> list[float]:
        """Normalize raw feature dict into a standard ordered vector using fitted mean/std."""
        vector: list[float] = []
        for key in self.feature_keys:
            val = raw_features.get(key, 0.0)
            mean = self.feature_means.get(key, 0.0)
            std = self.feature_stds.get(key, 1.0)
            norm_val = (val - mean) / std
            vector.append(norm_val)
        return vector

    def tokenize_sequence(self, sequence: list[str]) -> list[int]:
        """Convert action sequence into a padded sequence of integer token IDs."""
        tokens = [self.vocab.get(action, self.vocab["<UNK>"]) for action in sequence]
        # Truncate or pad to max_sequence_length
        if len(tokens) > self.max_sequence_length:
            tokens = tokens[: self.max_sequence_length]
        else:
            tokens = tokens + [self.vocab["<PAD>"]] * (self.max_sequence_length - len(tokens))
        return tokens
