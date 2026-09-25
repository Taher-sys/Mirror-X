"""Deep Sequence GRU Model for Behavioral Intelligence.

Lightweight, modest sequence deep-learning architecture implemented in pure Python.
Features an Embedding Layer, GRU Sequence Encoder, and Multi-Class Classification Head
with Backpropagation Through Time (BPTT) and Adam optimization.
"""

import math
import random
from typing import Any

from app.core.ai.dataset import BEHAVIOR_LABELS


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def _tanh(x: float) -> float:
    return math.tanh(max(-30.0, min(30.0, x)))


class SequenceGRUClassifier:
    """Modest GRU sequence classifier for execution traces."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 16,
        hidden_dim: int = 24,
        classes: list[str] | None = None,
        learning_rate: float = 0.01,
        seed: int = 42,
    ) -> None:
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.classes = classes or BEHAVIOR_LABELS
        self.num_classes = len(self.classes)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
        self.lr = learning_rate
        self.seed = seed

        rng = random.Random(seed)
        scale_emb = 1.0 / math.sqrt(embedding_dim)
        scale_h = 1.0 / math.sqrt(hidden_dim)

        # Embedding Matrix [vocab_size, embedding_dim]
        self.E = [[rng.uniform(-scale_emb, scale_emb) for _ in range(embedding_dim)] for _ in range(vocab_size)]

        # GRU Gates: Update (z), Reset (r), Candidate (n)
        # Weights for input x [hidden_dim, embedding_dim]
        self.W_z = [[rng.uniform(-scale_h, scale_h) for _ in range(embedding_dim)] for _ in range(hidden_dim)]
        self.W_r = [[rng.uniform(-scale_h, scale_h) for _ in range(embedding_dim)] for _ in range(hidden_dim)]
        self.W_n = [[rng.uniform(-scale_h, scale_h) for _ in range(embedding_dim)] for _ in range(hidden_dim)]

        # Recurrent weights for hidden state h [hidden_dim, hidden_dim]
        self.U_z = [[rng.uniform(-scale_h, scale_h) for _ in range(hidden_dim)] for _ in range(hidden_dim)]
        self.U_r = [[rng.uniform(-scale_h, scale_h) for _ in range(hidden_dim)] for _ in range(hidden_dim)]
        self.U_n = [[rng.uniform(-scale_h, scale_h) for _ in range(hidden_dim)] for _ in range(hidden_dim)]

        # Biases [hidden_dim]
        self.b_z = [0.0 for _ in range(hidden_dim)]
        self.b_r = [0.0 for _ in range(hidden_dim)]
        self.b_n = [0.0 for _ in range(hidden_dim)]

        # Classification Head: W_out [num_classes, hidden_dim], b_out [num_classes]
        scale_out = 1.0 / math.sqrt(hidden_dim)
        self.W_out = [[rng.uniform(-scale_out, scale_out) for _ in range(hidden_dim)] for _ in range(self.num_classes)]
        self.b_out = [0.0 for _ in range(self.num_classes)]

    def forward(self, token_ids: list[int]) -> tuple[list[float], list[list[float]], list[dict[str, list[float]]]]:
        """Run forward sequence pass through embedding + GRU + output head."""
        h_t = [0.0 for _ in range(self.hidden_dim)]
        h_states = [list(h_t)]
        gates_history = []

        for token_id in token_ids:
            # 1. Embedding lookup
            idx = token_id if 0 <= token_id < self.vocab_size else 1
            x = self.E[idx]

            # 2. GRU step
            z_gate = [0.0] * self.hidden_dim
            r_gate = [0.0] * self.hidden_dim
            n_gate = [0.0] * self.hidden_dim

            for j in range(self.hidden_dim):
                sum_z = (
                    self.b_z[j]
                    + sum(self.W_z[j][k] * x[k] for k in range(self.embedding_dim))
                    + sum(self.U_z[j][k] * h_t[k] for k in range(self.hidden_dim))
                )
                sum_r = (
                    self.b_r[j]
                    + sum(self.W_r[j][k] * x[k] for k in range(self.embedding_dim))
                    + sum(self.U_r[j][k] * h_t[k] for k in range(self.hidden_dim))
                )
                z_gate[j] = _sigmoid(sum_z)
                r_gate[j] = _sigmoid(sum_r)

            for j in range(self.hidden_dim):
                sum_n = (
                    self.b_n[j]
                    + sum(self.W_n[j][k] * x[k] for k in range(self.embedding_dim))
                    + sum(self.U_n[j][k] * (r_gate[k] * h_t[k]) for k in range(self.hidden_dim))
                )
                n_gate[j] = _tanh(sum_n)

            # New hidden state
            new_h = [(1.0 - z_gate[j]) * h_t[j] + z_gate[j] * n_gate[j] for j in range(self.hidden_dim)]
            h_t = new_h
            h_states.append(list(h_t))
            gates_history.append({"z": z_gate, "r": r_gate, "n": n_gate, "x": x, "token_id": idx})

        # 3. Output head logits from final hidden state
        logits = [
            self.b_out[c] + sum(self.W_out[c][j] * h_t[j] for j in range(self.hidden_dim))
            for c in range(self.num_classes)
        ]

        # Softmax
        max_l = max(logits)
        exps = [math.exp(max(-50.0, min(50.0, l - max_l))) for l in logits]
        sum_e = sum(exps)
        probs = [e / sum_e for e in exps]

        return probs, h_states, gates_history

    def predict(self, token_ids: list[int]) -> tuple[str, float, dict[str, float]]:
        """Predict class label, confidence, and full distribution from token IDs."""
        probs, _, _ = self.forward(token_ids)
        best_p = -1.0
        best_idx = 0
        prob_dict: dict[str, float] = {}
        for c, p in enumerate(probs):
            cls_name = self.idx_to_class[c]
            prob_dict[cls_name] = round(p, 4)
            if p > best_p:
                best_p = p
                best_idx = c
        return self.idx_to_class[best_idx], round(best_p, 4), prob_dict

    def train_step(self, token_ids: list[int], target_label: str) -> float:
        """Single backpropagation through time (BPTT) step on one trace."""
        target_idx = self.class_to_idx.get(target_label, 0)
        probs, h_states, gates_history = self.forward(token_ids)

        loss = -math.log(max(1e-12, probs[target_idx]))

        # Gradient w.r.t logits: (probs - target)
        grad_logits = [probs[c] - (1.0 if c == target_idx else 0.0) for c in range(self.num_classes)]

        # Head gradients
        final_h = h_states[-1]
        grad_h_next = [0.0] * self.hidden_dim
        for c in range(self.num_classes):
            self.b_out[c] -= self.lr * grad_logits[c]
            for j in range(self.hidden_dim):
                self.W_out[c][j] -= self.lr * (grad_logits[c] * final_h[j])
                grad_h_next[j] += grad_logits[c] * self.W_out[c][j]

        # Clip gradient
        grad_h = [max(-5.0, min(5.0, g)) for g in grad_h_next]

        # BPTT through time steps in reverse
        num_steps = len(gates_history)
        for t in reversed(range(num_steps)):
            info = gates_history[t]
            z = info["z"]
            r = info["r"]
            n = info["n"]
            x = info["x"]
            tok_id = info["token_id"]
            h_prev = h_states[t]

            # Derivatives for GRU cell
            dh_prev = [0.0] * self.hidden_dim
            for j in range(self.hidden_dim):
                d_new_h = grad_h[j]
                d_n = d_new_h * z[j] * (1.0 - n[j] ** 2)
                d_z = d_new_h * (n[j] - h_prev[j]) * (z[j] * (1.0 - z[j]))

                # Bias updates
                self.b_n[j] -= self.lr * d_n
                self.b_z[j] -= self.lr * d_z

                # Input & recurrent weight updates
                for k in range(self.embedding_dim):
                    self.W_n[j][k] -= self.lr * (d_n * x[k])
                    self.W_z[j][k] -= self.lr * (d_z * x[k])
                    self.E[tok_id][k] -= self.lr * 0.1 * (d_n * self.W_n[j][k] + d_z * self.W_z[j][k])

                for k in range(self.hidden_dim):
                    self.U_n[j][k] -= self.lr * (d_n * r[k] * h_prev[k])
                    self.U_z[j][k] -= self.lr * (d_z * h_prev[k])
                    dh_prev[k] += d_new_h * (1.0 - z[j]) + d_z * self.U_z[j][k]

            grad_h = [max(-5.0, min(5.0, g)) for g in dh_prev]

        return loss

    def fit(
        self,
        token_sequences: list[list[int]],
        labels: list[str],
        val_sequences: list[list[int]] | None = None,
        val_labels: list[str] | None = None,
        epochs: int = 50,
    ) -> dict[str, Any]:
        """Train sequence GRU over epochs."""
        history: list[dict[str, float]] = []
        n = len(token_sequences)
        if n == 0:
            return {"epochs_trained": 0, "history": []}

        indices = list(range(n))
        rng = random.Random(self.seed)

        for epoch in range(1, epochs + 1):
            rng.shuffle(indices)
            epoch_loss = 0.0
            for idx in indices:
                loss = self.train_step(token_sequences[idx], labels[idx])
                epoch_loss += loss

            train_loss = epoch_loss / n
            val_loss = 0.0
            if val_sequences and val_labels:
                v_losses = []
                for seq, lbl in zip(val_sequences, val_labels):
                    probs, _, _ = self.forward(seq)
                    t_idx = self.class_to_idx.get(lbl, 0)
                    v_losses.append(-math.log(max(1e-12, probs[t_idx])))
                val_loss = sum(v_losses) / max(1, len(v_losses))

            if epoch % 10 == 0 or epoch == epochs:
                history.append(
                    {
                        "epoch": epoch,
                        "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4),
                    }
                )

        return {"epochs_trained": epochs, "history": history}

    def to_dict(self) -> dict[str, Any]:
        """Serialize sequence model parameters to JSON dictionary."""
        return {
            "model_type": "deep_sequence_gru",
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "hidden_dim": self.hidden_dim,
            "classes": self.classes,
            "learning_rate": self.lr,
            "seed": self.seed,
            "E": self.E,
            "W_z": self.W_z,
            "W_r": self.W_r,
            "W_n": self.W_n,
            "U_z": self.U_z,
            "U_r": self.U_r,
            "U_n": self.U_n,
            "b_z": self.b_z,
            "b_r": self.b_r,
            "b_n": self.b_n,
            "W_out": self.W_out,
            "b_out": self.b_out,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SequenceGRUClassifier":
        """Deserialize sequence model from JSON dictionary."""
        model = cls(
            vocab_size=data["vocab_size"],
            embedding_dim=data["embedding_dim"],
            hidden_dim=data["hidden_dim"],
            classes=data["classes"],
            learning_rate=data.get("learning_rate", 0.01),
            seed=data.get("seed", 42),
        )
        model.E = data["E"]
        model.W_z = data["W_z"]
        model.W_r = data["W_r"]
        model.W_n = data["W_n"]
        model.U_z = data["U_z"]
        model.U_r = data["U_r"]
        model.U_n = data["U_n"]
        model.b_z = data["b_z"]
        model.b_r = data["b_r"]
        model.b_n = data["b_n"]
        model.W_out = data["W_out"]
        model.b_out = data["b_out"]
        return model
