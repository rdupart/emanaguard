"""Evaluation metrics: majority baseline, balanced accuracy, macro-F1, MI."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mutual_info_score,
)

# Axes with MI near this on null runs are labeled NULL (see phase1_eval)
MI_PASS_FLOOR_BITS = 0.15


@dataclass
class AxisResult:
    label_axis: str
    signal_set: str
    backend: str
    n_samples: int
    n_classes: int
    # Legacy field: now stores majority-class baseline (not 1/n_classes)
    chance_accuracy: float
    majority_baseline_accuracy: float
    uniform_chance_accuracy: float
    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    mi_bits: float
    ci_lower: float
    ci_upper: float
    balanced_ci_lower: float
    balanced_ci_upper: float
    pass_lower_ci_above_chance: bool  # legacy alias: pass_balanced_beat_majority
    pass_balanced_beat_majority: bool
    pass_mi_above_floor: bool
    pass_gate: bool
    confusion: list[list[int]]
    class_names: list[str]
    per_class_recall: dict[str, float] = field(default_factory=dict)
    per_class_support: dict[str, int] = field(default_factory=dict)
    claim_status: str = "PRELIMINARY"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "label_axis": self.label_axis,
            "signal_set": self.signal_set,
            "backend": self.backend,
            "n_samples": self.n_samples,
            "n_classes": self.n_classes,
            "chance_accuracy": self.majority_baseline_accuracy,
            "majority_baseline_accuracy": self.majority_baseline_accuracy,
            "uniform_chance_accuracy": self.uniform_chance_accuracy,
            "accuracy": self.accuracy,
            "balanced_accuracy": self.balanced_accuracy,
            "macro_f1": self.macro_f1,
            "mi_bits": self.mi_bits,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "balanced_ci_lower": self.balanced_ci_lower,
            "balanced_ci_upper": self.balanced_ci_upper,
            "pass_lower_ci_above_chance": self.pass_gate,
            "pass_balanced_beat_majority": self.pass_balanced_beat_majority,
            "pass_mi_above_floor": self.pass_mi_above_floor,
            "pass_gate": self.pass_gate,
            "confusion": self.confusion,
            "class_names": self.class_names,
            "per_class_recall": self.per_class_recall,
            "per_class_support": self.per_class_support,
            "claim_status": self.claim_status,
            "notes": self.notes,
        }


def chance_level(n_classes: int) -> float:
    """Uniform random baseline (reported for reference only)."""
    return 1.0 / max(n_classes, 1)


def majority_baseline(y_train: np.ndarray) -> float:
    y_train = np.asarray(y_train)
    if len(y_train) == 0:
        return 0.0
    _, counts = np.unique(y_train, return_counts=True)
    return float(np.max(counts) / len(y_train))


def bootstrap_metric_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.0
    vals = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        vals.append(float(metric_fn(y_true[idx], y_pred[idx])))
    if not vals:
        point = float(metric_fn(y_true, y_pred))
        return point, point, point
    arr = np.array(vals)
    point = float(metric_fn(y_true, y_pred))
    lo = float(np.percentile(arr, 100 * alpha / 2))
    hi = float(np.percentile(arr, 100 * (1 - alpha / 2)))
    return point, lo, hi


def bootstrap_accuracy_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    return bootstrap_metric_ci(
        y_true, y_pred, accuracy_score, n_bootstrap, seed, alpha
    )


def per_class_recall_dict(
    y_true: np.ndarray, y_pred: np.ndarray, class_names: list[str]
) -> tuple[dict[str, float], dict[str, int]]:
    cm = confusion_matrix(y_true, y_pred, labels=class_names)
    recalls: dict[str, float] = {}
    supports: dict[str, int] = {}
    for i, name in enumerate(class_names):
        row_sum = int(cm[i, :].sum()) if i < len(cm) else 0
        supports[str(name)] = row_sum
        if row_sum > 0 and i < len(cm):
            recalls[str(name)] = float(cm[i, i] / row_sum)
        else:
            recalls[str(name)] = 0.0
    return recalls, supports


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
    label_axis: str,
    signal_set: str,
    backend: str,
    y_train: np.ndarray | None = None,
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
    maj = majority_baseline(y_train if y_train is not None else y_true)
    uni = chance_level(len(corpus_labels) if corpus_labels else n_corpus)

    if n_present < 2:
        extra = notes or "NEGATIVE: test fold has a single class — axis not evaluable"
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y_true)),
            n_classes=n_present,
            chance_accuracy=maj,
            majority_baseline_accuracy=maj,
            uniform_chance_accuracy=uni,
            accuracy=float(np.mean(y_true == y_pred)) if len(y_true) else 0.0,
            balanced_accuracy=0.0,
            macro_f1=0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            balanced_ci_lower=0.0,
            balanced_ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            pass_balanced_beat_majority=False,
            pass_mi_above_floor=False,
            pass_gate=False,
            confusion=[[int(len(y_true))]] if len(y_true) else [[]],
            class_names=[str(c) for c in present],
            notes=extra,
        )

    label_order = corpus_labels if corpus_labels else [str(c) for c in present]
    acc, lo, hi = bootstrap_accuracy_ci(y_true, y_pred, n_bootstrap, seed)
    bal, bal_lo, bal_hi = bootstrap_metric_ci(
        y_true,
        y_pred,
        balanced_accuracy_score,
        n_bootstrap,
        seed + 1,
    )
    macro_f1 = float(
        f1_score(y_true, y_pred, average="macro", labels=label_order, zero_division=0)
    )
    mi = float(mutual_info_score(y_true, y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=label_order)
    recalls, supports = per_class_recall_dict(y_true, y_pred, label_order)
    pass_maj = bal_lo > maj
    pass_mi = mi >= MI_PASS_FLOOR_BITS
    pass_gate = pass_maj and pass_mi
    return AxisResult(
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
        n_samples=int(len(y_true)),
        n_classes=len(label_order),
        chance_accuracy=maj,
        majority_baseline_accuracy=maj,
        uniform_chance_accuracy=uni,
        accuracy=acc,
        balanced_accuracy=bal,
        macro_f1=macro_f1,
        mi_bits=mi,
        ci_lower=lo,
        ci_upper=hi,
        balanced_ci_lower=bal_lo,
        balanced_ci_upper=bal_hi,
        pass_lower_ci_above_chance=pass_gate,
        pass_balanced_beat_majority=pass_maj,
        pass_mi_above_floor=pass_mi,
        pass_gate=pass_gate,
        confusion=cm.tolist(),
        class_names=label_order,
        per_class_recall=recalls,
        per_class_support=supports,
        notes=notes,
    )
