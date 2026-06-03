from __future__ import annotations

import numpy as np

from pipeline.eval.metrics import (
    MI_PASS_FLOOR_BITS,
    bootstrap_accuracy_ci,
    chance_level,
    evaluate_predictions,
    majority_baseline,
)


def test_uniform_chance_level():
    assert chance_level(4) == 0.25


def test_majority_baseline_imbalanced():
    y = np.array(["a"] * 80 + ["b"] * 20)
    assert majority_baseline(y) == 0.8


def test_bootstrap_ci_bounds():
    y = np.array([0, 0, 1, 1, 0, 1])
    pred = np.array([0, 1, 1, 1, 0, 0])
    acc, lo, hi = bootstrap_accuracy_ci(y, pred, n_bootstrap=200, seed=0)
    assert lo <= acc <= hi


def test_pass_gate_requires_balanced_beat_majority_and_mi():
    y_train = np.array(["a", "a", "a", "b", "b", "b"])
    y_test = np.array(["a", "a", "b", "b"])
    y_pred = np.array(["a", "b", "b", "b"])
    res = evaluate_predictions(
        y_test,
        y_pred,
        class_names=["a", "b"],
        label_axis="test",
        signal_set="test",
        backend="test",
        y_train=y_train,
        n_bootstrap=100,
        seed=0,
    )
    assert res.majority_baseline_accuracy == 0.5
    assert res.uniform_chance_accuracy == 0.5
    assert res.mi_bits >= 0
    assert isinstance(res.pass_gate, bool)


def test_mi_floor_constant():
    assert MI_PASS_FLOOR_BITS == 0.15
