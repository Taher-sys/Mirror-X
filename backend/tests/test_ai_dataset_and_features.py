"""Unit tests for AI Core Behavior Dataset Generator and Feature Engineering."""

from app.core.ai.dataset import BEHAVIOR_LABELS, BehaviorDatasetGenerator
from app.core.ai.features import (
    FEATURE_DEFINITIONS,
    FEATURE_KEYS,
    BehavioralFeatureExtractor,
)


def test_dataset_generator_seed_reproducibility() -> None:
    """Verifies that the same seed produces identical synthetic examples."""
    gen1 = BehaviorDatasetGenerator(seed=42)
    ex1 = gen1.synthesize_example("successful", 0)

    gen2 = BehaviorDatasetGenerator(seed=42)
    ex2 = gen2.synthesize_example("successful", 0)

    assert ex1["action_sequence"] == ex2["action_sequence"]
    assert ex1["timing_features"] == ex2["timing_features"]
    assert ex1["behavioral_label"] == ex2["behavioral_label"]
    assert ex1["label_provenance"] == ex2["label_provenance"]


def test_dataset_generator_all_behavior_labels() -> None:
    """Verifies that all 7 behavioral labels are synthesized with appropriate provenance."""
    gen = BehaviorDatasetGenerator(seed=123)
    for label in BEHAVIOR_LABELS:
        ex = gen.synthesize_example(label, 1)
        assert ex["behavioral_label"] == label
        assert ex["label_provenance"] is not None
        assert len(ex["label_provenance"]) > 10
        assert "action_sequence" in ex
        assert len(ex["action_sequence"]) >= 2


def test_feature_extractor_definitions_and_keys() -> None:
    """Ensures all 21 extracted features are formally documented."""
    extractor = BehavioralFeatureExtractor()
    assert len(extractor.feature_keys) == 21
    for key in extractor.feature_keys:
        assert key in FEATURE_DEFINITIONS
        assert len(FEATURE_DEFINITIONS[key]) > 10


def test_feature_extraction_and_scaling() -> None:
    """Tests raw feature extraction, z-score fitting, and sequence tokenization."""
    gen = BehaviorDatasetGenerator(seed=99)
    extractor = BehavioralFeatureExtractor(max_sequence_length=10)

    examples = [gen.synthesize_example("successful", i) for i in range(10)]
    extractor.build_vocab_from_examples(examples)

    raw_features_list = [extractor.extract_raw_features(ex) for ex in examples]
    assert len(raw_features_list) == 10
    for raw in raw_features_list:
        assert len(raw) == len(FEATURE_KEYS)
        assert raw["action_sequence_length"] >= 2.0
        assert raw["sandbox_access_ratio"] == 1.0

    extractor.fit_scaler(raw_features_list)
    assert len(extractor.feature_means) == len(FEATURE_KEYS)
    assert len(extractor.feature_stds) == len(FEATURE_KEYS)

    # Test normalization
    norm_vec = extractor.transform_features(raw_features_list[0])
    assert len(norm_vec) == len(FEATURE_KEYS)
    assert all(isinstance(v, float) for v in norm_vec)

    # Test sequence tokenization
    seq = ["query_database", "read_file", "unknown_action_xyz"]
    tokens = extractor.tokenize_sequence(seq)
    assert len(tokens) == 10
    assert tokens[0] == extractor.vocab["query_database"]
    assert tokens[1] == extractor.vocab["read_file"]
    assert tokens[2] == extractor.vocab["<UNK>"]
    assert tokens[3:] == [extractor.vocab["<PAD>"]] * 7


def test_entropy_and_repetition_metrics() -> None:
    """Verifies Shannon entropy and consecutive repeat calculations."""
    extractor = BehavioralFeatureExtractor()

    # Deterministic sequence: always same tool -> entropy = 0.0
    zero_entropy = extractor.compute_entropy(["read_file", "read_file", "read_file"])
    assert zero_entropy == 0.0

    # Diverse sequence -> entropy > 0.0
    diverse_entropy = extractor.compute_entropy(["query_database", "read_file", "write_file", "http_request"])
    assert diverse_entropy == 2.0

    # Repetition
    repeats = extractor.compute_max_consecutive_repeats(["a", "b", "b", "b", "c"])
    assert repeats == 3
