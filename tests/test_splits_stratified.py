from __future__ import annotations

import numpy as np

from pipeline.eval.splits import split_by_config_stratified


def test_stratified_holdout_includes_multiple_llm_phases():
    config_ids = np.array(
        ["w04"] * 5 + ["w08"] * 5 + ["w10"] * 5 + ["w11"] * 5
    )
    y = np.array(["n/a"] * 5 + ["n/a"] * 5 + ["prefill"] * 5 + ["decode"] * 5)
    _, test_m = split_by_config_stratified(config_ids, y, holdout_fraction=0.25, seed=0)
    test_labels = set(y[test_m])
    assert len(test_labels) >= 2
