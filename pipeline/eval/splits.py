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


def split_by_config_stratified(
    config_ids: np.ndarray,
    y: np.ndarray,
    holdout_fraction: float = 0.25,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Hold out whole configs but keep ≥1 config per label value in test when possible.
    Avoids degenerate test folds (e.g. llm_phase test set only 'n/a').
    """
    from collections import defaultdict

    config_ids = np.asarray(config_ids)
    y = np.asarray(y)
    config_label: dict[str, str] = {}
    for cid, lab in zip(config_ids, y):
        config_label[str(cid)] = str(lab)

    by_label: dict[str, list[str]] = defaultdict(list)
    for cid, lab in config_label.items():
        by_label[lab].append(cid)

    rng = np.random.default_rng(seed)
    test_configs: set[str] = set()
    for lab, configs in by_label.items():
        configs = list(configs)
        rng.shuffle(configs)
        n_test = max(1, int(len(configs) * holdout_fraction))
        test_configs.update(configs[:n_test])

    train_m = np.array([str(c) not in test_configs for c in config_ids])
    test_m = ~train_m
    return train_m, test_m


def split_holdout_architectures(
    architecture_ids: np.ndarray,
    holdout_fraction: float = 0.25,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Hold out entire architecture_id values (unseen models in test)."""
    architecture_ids = np.asarray(architecture_ids)
    uniq = sorted(set(architecture_ids))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_test = max(1, int(len(uniq) * holdout_fraction))
    held_out = list(uniq[:n_test])
    test_set = set(held_out)
    train_m = np.array([a not in test_set for a in architecture_ids])
    test_m = ~train_m
    return train_m, test_m, held_out


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
