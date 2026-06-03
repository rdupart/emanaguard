"""Corpus scale and held-out architecture split hygiene."""

from __future__ import annotations

import numpy as np

from pipeline.eval.splits import split_holdout_architectures
from pipeline.workloads.corpus import (
    MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
    all_architecture_ids,
    corpus_size,
    iter_corpus,
)


def test_corpus_has_at_least_ten_architectures():
    assert len(all_architecture_ids()) >= 10


def test_corpus_size_at_least_24_configs():
    assert corpus_size() >= 24


def test_hard_case_train_volume_matched_across_archs():
    trains = [s for s in iter_corpus() if s.volume_profile == "hard_case_train"]
    assert len(trains) == len(all_architecture_ids())
    bss = {s.batch_size for s in trains}
    sls = {s.seq_length for s in trains}
    steps = {s.steps for s in trains}
    assert bss == {4}
    assert sls == {128}
    assert steps == {6}


def test_holdout_leaves_at_least_two_train_architectures_when_possible():
    archs = [f"arch_{i}" for i in range(10)]
    arch_ids = np.array(archs * 3)
    train_m, test_m, held = split_holdout_architectures(
        arch_ids, holdout_fraction=0.25, seed=0, min_train_architectures=2
    )
    assert len(set(arch_ids[train_m])) >= 2
    assert len(held) >= 1
    assert not set(held) & set(arch_ids[train_m])


def test_holdout_with_only_two_architectures_cannot_train_two_classes():
    arch_ids = np.array(["a", "a", "b", "b"])
    train_m, _, held = split_holdout_architectures(arch_ids, holdout_fraction=0.5, seed=1)
    train_classes = len(set(arch_ids[train_m]))
    assert train_classes <= 1 or len(held) == 0


def test_min_architectures_constant_is_eight():
    assert MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM == 8
