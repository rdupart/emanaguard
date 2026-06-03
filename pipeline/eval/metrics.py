"""Evaluation metrics: accuracy vs chance, MI, bootstrap CIs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, mutual_info_score


@dataclass
class AxisResult:
    label_axis: str
    signal_set: str  # "vm_ground_truth" | "host_observer"
    backend: str
    n_samples: int
    n_classes: int
    chance_accuracy: float
    accuracy: float
    mi_bits: float
    ci_lower: float
    ci_upper: float
    pass_lower_ci_above_chance: bool
    confusion: list[list[int]]
    class_names: list[str]
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "label_axis": self.label_axis,
            "signal_set": self.signal_set,
            "backend": self.backend,
            "n_samples": self.n_samples,
            "n_classes": self.n_classes,
            "chance_accuracy": self.chance_accuracy,
            "accuracy": self.accuracy,
            "mi_bits": self.mi_bits,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "pass_lower_ci_above_chance": self.pass_lower_ci_above_chance,
            "confusion": self.confusion,
            "class_names": self.class_names,
            "notes": self.notes,
        }


def chance_level(n_classes: int) -> float:
    return 1.0 / max(n_classes, 1)


def bootstrap_accuracy_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.0
    accs = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        accs.append(accuracy_score(y_true[idx], y_pred[idx]))
    accs_arr = np.array(accs)
    point = accuracy_score(y_true, y_pred)
    lo = float(np.percentile(accs_arr, 100 * alpha / 2))
    hi = float(np.percentile(accs_arr, 100 * (1 - alpha / 2)))
    return point, lo, hi


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
    label_axis: str,
    signal_set: str,
    backend: str,
    n_bootstrap: int = 1000,
    seed: int = 42,
    notes: str = "",
    all_labels: list[str] | None = None,
) -> AxisResult:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    corpus_labels = sorted(
        set(class_names) | set(all_labels or []) | set(y_true) | set(y_pred),
        key=str,
    )
    present = np.unique(y_true)
    n_present = len(present)
    n_corpus = max(len(corpus_labels), n_present)

    if n_present < 2:
        extra = notes or "NEGATIVE: test fold has a single class — axis not evaluable"
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y_true)),
            n_classes=n_present,
            chance_accuracy=chance_level(n_corpus),
            accuracy=float(np.mean(y_true == y_pred)) if len(y_true) else 0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            confusion=[[int(len(y_true))]] if len(y_true) else [[]],
            class_names=[str(c) for c in present],
            notes=extra,
        )

    label_order = corpus_labels if corpus_labels else [str(c) for c in present]
    acc, lo, hi = bootstrap_accuracy_ci(y_true, y_pred, n_bootstrap, seed)
    mi = float(mutual_info_score(y_true, y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=label_order)
    ch = chance_level(len(label_order))
    return AxisResult(
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
        n_samples=int(len(y_true)),
        n_classes=len(label_order),
        chance_accuracy=ch,
        accuracy=acc,
        mi_bits=mi,
        ci_lower=lo,
        ci_upper=hi,
        pass_lower_ci_above_chance=(lo > ch),
        confusion=cm.tolist(),
        class_names=label_order,
        notes=notes,
    )
