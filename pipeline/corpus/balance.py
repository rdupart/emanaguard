"""Balanced subsampling of physical runs / configs for fair per-class metrics."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from pipeline.trace.events import RunLabels, TransferEvent


def label_counts_physical(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    label_fn,
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for _, lb in runs:
        counts[str(label_fn(lb))] += 1
    return dict(counts)


def subsample_physical_runs_balanced(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    label_fn,
    seed: int = 42,
) -> tuple[list[tuple[list[TransferEvent], RunLabels]], dict]:
    """
    Downsample physical base captures so each label value has the same count.
    """
    rng = np.random.default_rng(seed)
    by_lab: dict[str, list[tuple[list[TransferEvent], RunLabels]]] = defaultdict(list)
    for run in runs:
        by_lab[str(label_fn(run[1]))].append(run)
    if not by_lab:
        return runs, {"status": "empty"}
    n_min = min(len(v) for v in by_lab.values())
    out: list = []
    per_class = {}
    for lab, group in by_lab.items():
        idx = np.arange(len(group))
        rng.shuffle(idx)
        take = [group[i] for i in idx[:n_min]]
        out.extend(take)
        per_class[lab] = n_min
    rng.shuffle(out)
    meta = {
        "status": "balanced_subsample",
        "per_class_counts": per_class,
        "n_per_class": n_min,
        "n_total": len(out),
        "n_before": len(runs),
    }
    return out, meta


def subsample_indices_balanced(
    y: np.ndarray,
    config_ids: np.ndarray,
    seed: int = 42,
) -> np.ndarray:
    """
    Return boolean mask selecting rows so each label has equal config counts.
    Groups by unique config_id per label (one label per config assumed).
    """
    rng = np.random.default_rng(seed)
    config_label: dict[str, str] = {}
    for cid, lab in zip(config_ids, y):
        config_label[str(cid)] = str(lab)
    by_lab: dict[str, list[str]] = defaultdict(list)
    for cid, lab in config_label.items():
        by_lab[lab].append(cid)
    if not by_lab:
        return np.ones(len(y), dtype=bool)
    n_min = min(len(v) for v in by_lab.values())
    keep_configs: set[str] = set()
    for lab, configs in by_lab.items():
        configs = list(configs)
        rng.shuffle(configs)
        keep_configs.update(configs[:n_min])
    return np.array([str(c) in keep_configs for c in config_ids])
