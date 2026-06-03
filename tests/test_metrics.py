from __future__ import annotations

import numpy as np

from pipeline.eval.metrics import bootstrap_accuracy_ci, chance_level


def test_chance_level():
    assert chance_level(4) == 0.25


def test_bootstrap_ci_bounds():
    y = np.array([0, 0, 1, 1, 0, 1])
    pred = np.array([0, 1, 1, 1, 0, 0])
    acc, lo, hi = bootstrap_accuracy_ci(y, pred, n_bootstrap=200, seed=0)
    assert lo <= acc <= hi
