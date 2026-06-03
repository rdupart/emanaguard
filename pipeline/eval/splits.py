"""Train/test hygiene — hold out entire seeds (different runs)."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def split_by_seed(
    seeds: Sequence[int],
    holdout_fraction: float = 0.25,
    seed_for_split: int = 0,
) -> tuple[list[int], list[int]]:
    rng = np.random.default_rng(seed_for_split)
    shuffled = list(seeds)
    rng.shuffle(shuffled)
    n_test = max(1, int(len(shuffled) * holdout_fraction))
    test_seeds = shuffled[:n_test]
    train_seeds = shuffled[n_test:]
    if not train_seeds:
        train_seeds = test_seeds[:-1]
        test_seeds = test_seeds[-1:]
    return train_seeds, test_seeds


def mask_for_seeds(all_seeds: np.ndarray, selected: list[int]) -> np.ndarray:
    return np.isin(all_seeds, selected)
