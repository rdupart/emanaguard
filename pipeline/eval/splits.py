"""Train/test hygiene — group by base capture, not random observations."""

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


def split_by_config(
    config_ids: Sequence[str],
    holdout_fraction: float = 0.25,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Hold out entire workload configs (all seeds/repetitions)."""
    uniq = sorted(set(config_ids))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_test = max(2, int(len(uniq) * holdout_fraction))
    test_set = set(uniq[:n_test])
    train_m = np.array([c not in test_set for c in config_ids])
    test_m = ~train_m
    return train_m, test_m


def split_by_base_run(
    base_run_ids: Sequence[str],
    holdout_fraction: float = 0.2,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """All observation replicas of a base capture stay in the same fold."""
    uniq = sorted(set(base_run_ids))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_test = max(1, int(len(uniq) * holdout_fraction))
    test_set = set(uniq[:n_test])
    train_m = np.array([b not in test_set for b in base_run_ids])
    test_m = ~train_m
    return train_m, test_m
