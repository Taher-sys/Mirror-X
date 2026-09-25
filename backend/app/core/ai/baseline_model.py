"""Transparent Baseline Model for Behavioral Intelligence.

Pure Python standard library implementation of a Multi-Class Softmax Logistic Classifier
and a Centroid-based Anomaly Detector. Includes comprehensive evaluation metrics
(precision, recall, F1, confusion matrix, false-positive analysis).
"""

import math
import random
from typing import Any

from app.core.ai.dataset import BEHAVIOR_LABELS


def train_val_test_split(
    items: list[Any],
    test_ratio: float = 0.2,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[Any], list[Any], list[Any]]:
    """Deterministically partition dataset into train, validation, and test splits."""
    shuffled = list(items)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)
    n_train = n - n_test - n_val

    train_data = shuffled[:n_train]
    val_data = shuffled[n_train : n_train + n_val]
    test_data = shuffled[n_train + n_val :]
    return train_data, val_data, test_data


def compute_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Compute comprehensive evaluation metrics: Precision, Recall, F1, Confusion Matrix, False Positive Analysis."""
    if labels is None:
        labels = BEHAVIOR_LABELS

    n = len(y_true)
    if n == 0:
        return {"accuracy": 0.0, "f1_macro": 0.0}

    # Confusion matrix: rows = true, cols = predicted
    matrix: dict[str, dict[str, int]] = {l: dict.fromkeys(labels, 0) for l in labels}
    for yt, yp in zip(y_true, y_pred):
        if yt in matrix and yp in matrix[yt]:
            matrix[yt][yp] += 1

    per_class: dict[str, dict[str, float]] = {}
    macro_precisions: list[float] = []
    macro_recalls: list[float] = []
    macro_f1s: list[float] = []
    false_positive_cases: list[dict[str, str]] = []

    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        tn = n - tp - fp - fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        support = sum(matrix[label].values())

        per_class[label] = {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "support": support,
        }

        if support > 0:
            macro_precisions.append(prec)
            macro_recalls.append(rec)
            macro_f1s.append(f1)

    # Collect detailed false positive instances
    for idx, (yt, yp) in enumerate(zip(y_true, y_pred)):
        if yt != yp:
            false_positive_cases.append(
                {
                    "sample_index": idx,
                    "ground_truth": yt,
                    "model_prediction": yp,
                    "type": f"False {yp} (True: {yt})",
                }
            )

    total_correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = total_correct / n

    macro_f1 = sum(macro_f1s) / len(macro_f1s) if macro_f1s else 0.0
    macro_p = sum(macro_precisions) / len(macro_precisions) if macro_precisions else 0.0
    macro_r = sum(macro_recalls) / len(macro_recalls) if macro_recalls else 0.0

    return {
        "total_samples": n,
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": matrix,
        "false_positive_analysis": {
            "total_misclassifications": len(false_positive_cases),
            "misclassification_rate": round((n - total_correct) / n, 4),
            "sample_errors": false_positive_cases[:10],
        },
    }


class BaselineLogisticClassifier:
    """Transparent Multi-Class Softmax Logistic Classifier with L2 Regularization."""

    def __init__(
        self,
        num_features: int,
        classes: list[str] | None = None,
        learning_rate: float = 0.05,
        l2_reg: float = 0.001,
        seed: int = 42,
    ) -> None:
        self.num_features = num_features
        self.classes = classes or BEHAVIOR_LABELS
        self.num_classes = len(self.classes)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
        self.lr = learning_rate
        self.l2_reg = l2_reg
        self.seed = seed

        # Initialize weights with small normal values and biases to 0
        rng = random.Random(seed)
        self.weights = [[(rng.gauss(0.0, 0.05)) for _ in range(self.num_classes)] for _ in range(self.num_features)]
        self.biases = [0.0 for _ in range(self.num_classes)]

    def _softmax(self, logits: list[float]) -> list[float]:
        """Numerically stable softmax."""
        max_val = max(logits)
        exps = [math.exp(max(-50.0, min(50.0, z - max_val))) for z in logits]
        sum_exp = sum(exps)
        return [e / sum_exp for e in exps]

    def forward(self, x: list[float]) -> list[float]:
        """Compute class probabilities for a single feature vector."""
        logits: list[float] = [self.biases[c] for c in range(self.num_classes)]
        for d in range(self.num_features):
            val = x[d]
            for c in range(self.num_classes):
                logits[c] += val * self.weights[d][c]
        return self._softmax(logits)

    def predict(self, x: list[float]) -> tuple[str, float, dict[str, float]]:
        """Predict class label, confidence, and full probability distribution."""
        probs = self.forward(x)
        max_prob = -1.0
        best_idx = 0
        prob_dict: dict[str, float] = {}
        for c, p in enumerate(probs):
            cls_name = self.idx_to_class[c]
            prob_dict[cls_name] = round(p, 4)
            if p > max_prob:
                max_prob = p
                best_idx = c
        return self.idx_to_class[best_idx], round(max_prob, 4), prob_dict

    def train_epoch(self, X: list[list[float]], y: list[str]) -> float:
        """Perform one training epoch over the dataset using mini-batch gradient updates."""
        n = len(X)
        if n == 0:
            return 0.0

        # Accumulated gradients
        grad_w = [[0.0 for _ in range(self.num_classes)] for _ in range(self.num_features)]
        grad_b = [0.0 for _ in range(self.num_classes)]
        total_loss = 0.0

        for x_vec, label in zip(X, y):
            probs = self.forward(x_vec)
            target_idx = self.class_to_idx.get(label, 0)

            # Cross entropy loss
            target_prob = max(1e-12, probs[target_idx])
            total_loss -= math.log(target_prob)

            # Gradient of cross-entropy w.r.t logits is (probs - one_hot)
            for c in range(self.num_classes):
                error = probs[c] - (1.0 if c == target_idx else 0.0)
                grad_b[c] += error
                for d in range(self.num_features):
                    grad_w[d][c] += error * x_vec[d]

        # Apply gradients with L2 regularization
        inv_n = 1.0 / n
        for c in range(self.num_classes):
            self.biases[c] -= self.lr * (grad_b[c] * inv_n)
            for d in range(self.num_features):
                reg = self.l2_reg * self.weights[d][c]
                self.weights[d][c] -= self.lr * ((grad_w[d][c] * inv_n) + reg)

        # Add L2 penalty to loss
        l2_penalty = (
            0.5
            * self.l2_reg
            * sum(self.weights[d][c] ** 2 for d in range(self.num_features) for c in range(self.num_classes))
        )
        return (total_loss / n) + l2_penalty

    def fit(
        self,
        X_train: list[list[float]],
        y_train: list[str],
        X_val: list[list[float]] | None = None,
        y_val: list[str] | None = None,
        epochs: int = 80,
    ) -> dict[str, Any]:
        """Fit model over multiple epochs and return training history."""
        history: list[dict[str, float]] = []
        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(X_train, y_train)
            val_loss = 0.0
            if X_val and y_val:
                val_losses = []
                for x_v, y_v in zip(X_val, y_val):
                    probs = self.forward(x_v)
                    target_idx = self.class_to_idx.get(y_v, 0)
                    val_losses.append(-math.log(max(1e-12, probs[target_idx])))
                val_loss = sum(val_losses) / max(1, len(val_losses))

            if epoch % 10 == 0 or epoch == epochs:
                history.append(
                    {
                        "epoch": epoch,
                        "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4),
                    }
                )

        return {"epochs_trained": epochs, "history": history}

    def get_feature_coefficients(self, feature_names: list[str]) -> dict[str, dict[str, float]]:
        """Explainable AI: Return weight coefficients connecting each feature to each class."""
        coefs: dict[str, dict[str, float]] = {}
        for d, name in enumerate(feature_names[: self.num_features]):
            coefs[name] = {self.idx_to_class[c]: round(self.weights[d][c], 4) for c in range(self.num_classes)}
        return coefs

    def to_dict(self) -> dict[str, Any]:
        """Serialize model parameters to plain JSON-compatible dictionary."""
        return {
            "model_type": "baseline_logistic",
            "num_features": self.num_features,
            "classes": self.classes,
            "learning_rate": self.lr,
            "l2_reg": self.l2_reg,
            "seed": self.seed,
            "weights": self.weights,
            "biases": self.biases,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineLogisticClassifier":
        """Deserialize model from dictionary."""
        model = cls(
            num_features=data["num_features"],
            classes=data["classes"],
            learning_rate=data.get("learning_rate", 0.05),
            l2_reg=data.get("l2_reg", 0.001),
            seed=data.get("seed", 42),
        )
        model.weights = data["weights"]
        model.biases = data["biases"]
        return model


class CentroidAnomalyDetector:
    """Computes normalized distance against the centroid of normal compliant runs."""

    def __init__(self, num_features: int) -> None:
        self.num_features = num_features
        self.centroid: list[float] = [0.0] * num_features
        self.variances: list[float] = [1.0] * num_features
        self.threshold: float = 3.0  # Normalized distance standard deviations

    def fit(self, normal_vectors: list[list[float]]) -> None:
        """Calculate mean centroid and variance for normal execution vectors."""
        n = len(normal_vectors)
        if n == 0:
            return
        for d in range(self.num_features):
            vals = [vec[d] for vec in normal_vectors]
            mean = sum(vals) / n
            var = sum((x - mean) ** 2 for x in vals) / max(1, n - 1)
            self.centroid[d] = mean
            self.variances[d] = max(1e-4, var)

    def score(self, x: list[float]) -> tuple[float, bool]:
        """Compute anomaly distance and binary flag."""
        dist_sq = sum(((x[d] - self.centroid[d]) ** 2) / self.variances[d] for d in range(self.num_features))
        dist = math.sqrt(dist_sq)
        # Map distance to 0..1 confidence using sigmoid
        prob_anomaly = 1.0 / (1.0 + math.exp(-0.8 * (dist - self.threshold)))
        is_anomaly = dist > self.threshold
        return round(prob_anomaly, 4), is_anomaly
