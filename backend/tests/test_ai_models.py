"""Unit tests for baseline logistic classifier, anomaly detector, metrics, and sequence GRU."""

from app.core.ai.baseline_model import (
    BaselineLogisticClassifier,
    CentroidAnomalyDetector,
    compute_metrics,
    train_val_test_split,
)
from app.core.ai.dataset import BEHAVIOR_LABELS
from app.core.ai.sequence_model import SequenceGRUClassifier


def test_train_val_test_split_reproducibility() -> None:
    """Verifies partition proportions and seeded reproducibility."""
    items = list(range(100))
    train1, val1, test1 = train_val_test_split(items, test_ratio=0.2, val_ratio=0.15, seed=42)
    train2, val2, test2 = train_val_test_split(items, test_ratio=0.2, val_ratio=0.15, seed=42)

    assert len(test1) == 20
    assert len(val1) == 15
    assert len(train1) == 65
    assert train1 == train2
    assert val1 == val2
    assert test1 == test2


def test_compute_metrics_and_confusion_matrix() -> None:
    """Tests accuracy, macro/weighted precision/recall/F1, and confusion matrix calculation."""
    y_true = ["successful", "failed", "policy_violation", "successful"]
    y_pred = ["successful", "failed", "failed", "successful"]

    metrics = compute_metrics(y_true, y_pred, BEHAVIOR_LABELS)
    assert metrics["total_samples"] == 4
    assert metrics["accuracy"] == 0.75
    assert "macro_f1" in metrics
    assert "confusion_matrix" in metrics
    assert "false_positive_analysis" in metrics
    assert metrics["false_positive_analysis"]["total_misclassifications"] == 1


def test_baseline_logistic_fit_predict_serialize() -> None:
    """Tests training of BaselineLogisticClassifier, prediction, and serialization."""
    num_features = 5
    classifier = BaselineLogisticClassifier(
        num_features=num_features,
        classes=["successful", "failed"],
        learning_rate=0.1,
        seed=42,
    )

    # Synthetic separable data: feature 0 is high for 'successful', low for 'failed'
    X_train = [
        [2.0, 1.0, 0.5, 0.0, 1.0],
        [2.5, 1.2, 0.6, 0.1, 1.1],
        [-2.0, -1.0, -0.5, 0.0, -1.0],
        [-2.5, -1.2, -0.6, -0.1, -1.1],
    ]
    y_train = ["successful", "successful", "failed", "failed"]

    history = classifier.fit(X_train, y_train, epochs=40)
    assert history["epochs_trained"] == 40
    assert history["history"][-1]["train_loss"] < history["history"][0]["train_loss"]

    # Predict positive
    pred, conf, probs = classifier.predict([2.2, 1.1, 0.5, 0.0, 1.0])
    assert pred == "successful"
    assert conf > 0.6

    # Explainability
    coefs = classifier.get_feature_coefficients(["f0", "f1", "f2", "f3", "f4"])
    assert "f0" in coefs
    assert "successful" in coefs["f0"]

    # Serialization
    data = classifier.to_dict()
    loaded = BaselineLogisticClassifier.from_dict(data)
    pred2, conf2, _ = loaded.predict([2.2, 1.1, 0.5, 0.0, 1.0])
    assert pred == pred2
    assert conf == conf2


def test_centroid_anomaly_detector() -> None:
    """Tests CentroidAnomalyDetector fitting and out-of-distribution detection."""
    detector = CentroidAnomalyDetector(num_features=3)
    normal_data = [
        [1.0, 1.0, 1.0],
        [1.1, 0.9, 1.0],
        [0.9, 1.0, 1.1],
        [1.0, 1.1, 0.9],
    ]
    detector.fit(normal_data)

    # In-distribution point
    conf_in, is_anom_in = detector.score([1.0, 1.0, 1.0])
    assert not is_anom_in
    assert conf_in < 0.5

    # Out-of-distribution anomaly point
    conf_out, is_anom_out = detector.score([25.0, -30.0, 50.0])
    assert is_anom_out
    assert conf_out > 0.8


def test_sequence_gru_fit_predict_serialize() -> None:
    """Tests SequenceGRUClassifier forward pass, BPTT training, prediction, and serialization."""
    vocab_size = 8
    model = SequenceGRUClassifier(
        vocab_size=vocab_size,
        embedding_dim=8,
        hidden_dim=12,
        classes=["successful", "policy_violation"],
        learning_rate=0.05,
        seed=42,
    )

    # Sequences: [2, 3, 2] is successful, [6, 7, 6] is policy_violation
    train_seqs = [
        [2, 3, 2, 0],
        [2, 2, 3, 0],
        [6, 7, 6, 0],
        [7, 6, 7, 0],
    ]
    train_labels = ["successful", "successful", "policy_violation", "policy_violation"]

    res = model.fit(train_seqs, train_labels, epochs=30)
    assert res["epochs_trained"] == 30

    pred, conf, probs = model.predict([2, 3, 2, 0])
    assert pred in ("successful", "policy_violation")
    assert "successful" in probs
    assert "policy_violation" in probs

    # Serialization
    m_dict = model.to_dict()
    loaded = SequenceGRUClassifier.from_dict(m_dict)
    l_pred, l_conf, _ = loaded.predict([2, 3, 2, 0])
    assert pred == l_pred
    assert conf == l_conf
