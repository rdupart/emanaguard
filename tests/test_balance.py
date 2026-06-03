from __future__ import annotations

import numpy as np

from pipeline.corpus.balance import subsample_indices_balanced


def test_subsample_balanced_configs():
    config_ids = np.array(["c1", "c1", "c2", "c2", "c3", "c3"])
    y = np.array(["a", "a", "a", "a", "b", "b"])
    m = subsample_indices_balanced(y, config_ids, seed=0)
    assert m.sum() == 4
