"""Phase 2 detector — trivial vs hard violation suites (preliminary)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, confusion_matrix, roc_curve

from detector.covert_modulator import apply_covert_modulator
from detector.policy import AttestedPolicy, violation_label
from pipeline.corpus.expand import expand_observations
from pipeline.eval.splits import split_by_base_run
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import apply_realistic_observer, realistic_observer_features
from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import (
    ARCHITECTURE_SPECS,
    HARD_CASE_TRAIN_BS,
    HARD_CASE_TRAIN_SL,
    MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
)

# Single attested architecture at train + volume-matched profile (hard-case policy)
HARD_DETECTOR_POLICY = AttestedPolicy(
    name="train_volume_matched_arch_mlp_256x4_only",
    allowed_modes=frozenset({"train"}),
    allowed_architectures=frozenset({"arch_mlp_256x4"}),
)


class ViolationSuite(str, Enum):
    TRIVIAL_MODE = "trivial_mode_change"
    HARD_WRONG_ARCH = "hard_unauthorized_architecture"
    HARD_COVERT_MOD = "hard_covert_modulator"


@dataclass
class DetectorResult:
    suite: str
    policy_name: str
    signal_set: str
    backend: str
    roc_auc: float
    fpr_at_threshold: float
    tpr_at_threshold: float
    threshold: float
    false_positives: int
    true_positives: int
    false_negatives: int
    true_negatives: int
    n_test: int
    headline: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _resolve_attested_architecture(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    policy: AttestedPolicy,
) -> str | None:
    """Pick attested architecture: policy preference, else dominant train @ volume-matched profile."""
    present = {lb.architecture_id or lb.model_class for _, lb in runs}
    for arch in policy.allowed_architectures:
        if arch in present:
            return arch
    matched = [
        lb.architecture_id or lb.model_class
        for _, lb in runs
        if lb.mode == "train"
        and lb.batch_size == HARD_CASE_TRAIN_BS
        and lb.seq_length == HARD_CASE_TRAIN_SL
    ]
    if not matched:
        return None
    vals, counts = np.unique(matched, return_counts=True)
    return str(vals[int(np.argmax(counts))])


def _volume_matched_train(labels: RunLabels) -> bool:
    return (
        labels.mode == "train"
        and labels.batch_size == HARD_CASE_TRAIN_BS
        and labels.seq_length == HARD_CASE_TRAIN_SL
    )


def _rng_for(labels: RunLabels) -> np.random.Generator:
    return np.random.default_rng(
        hash((labels.base_run_id, labels.observation_idx)) & 0xFFFFFFFF
    )


def _features(events: list[TransferEvent], labels: RunLabels) -> np.ndarray:
    host = project_host_observer(events)
    obs = apply_realistic_observer(host, _rng_for(labels))
    return host_observer_feature_vector(obs)


def _suite_label(
    labels: RunLabels,
    suite: ViolationSuite,
    policy: AttestedPolicy,
    *,
    modulated_events: list[dict] | None = None,
) -> int:
    if suite == ViolationSuite.TRIVIAL_MODE:
        return 0 if labels.mode == "train" else 1
    if suite == ViolationSuite.HARD_WRONG_ARCH:
        if labels.mode != "train":
            return 0
        arch = labels.architecture_id or labels.model_class
        return 0 if arch == "arch_mlp_256x4" else 1
    if suite == ViolationSuite.HARD_COVERT_MOD:
        return 1 if modulated_events is not None else 0
    return violation_label(labels, policy)


def _build_rows(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    suite: ViolationSuite,
    policy: AttestedPolicy,
    *,
    attested_arch: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xs, ys, bases = [], [], []
    attested = attested_arch or _resolve_attested_architecture(runs, policy)
    for events, labels in runs:
        if labels.observation_idx != 0:
            continue
        arch = labels.architecture_id or labels.model_class
        if suite == ViolationSuite.HARD_COVERT_MOD:
            if not attested or not _volume_matched_train(labels) or arch != attested:
                continue
            host = project_host_observer(events)
            xs.append(_features(events, labels))
            ys.append(0)
            bases.append(labels.base_run_id)
            mod = apply_covert_modulator(host, _rng_for(labels))
            xs.append(host_observer_feature_vector(mod))
            ys.append(1)
            bases.append(labels.base_run_id + ":covert")
            continue
        elif suite == ViolationSuite.HARD_WRONG_ARCH:
            if not _volume_matched_train(labels):
                continue
            if not attested:
                continue
            x = _features(events, labels)
            y = 0 if arch == attested else 1
        else:
            x = _features(events, labels)
            y = _suite_label(labels, suite, policy)
        xs.append(x)
        ys.append(y)
        bases.append(labels.base_run_id)
    if not xs:
        return np.empty((0, 0)), np.array([], dtype=int), np.array([], dtype=object)
    return np.vstack(xs), np.array(ys), np.array(bases)


def _eval_suite(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    suite: ViolationSuite,
    policy: AttestedPolicy,
    backend: str,
    seed: int,
    headline: bool,
    *,
    attested_arch: str | None = None,
) -> DetectorResult:
    attested = attested_arch or _resolve_attested_architecture(runs, policy)
    x, y, bases = _build_rows(runs, suite, policy, attested_arch=attested)
    if x.size == 0 or len(np.unique(y)) < 2 or len(x) < 8:
        return DetectorResult(
            suite=suite.value,
            policy_name=policy.name,
            signal_set="host_observer_realistic_single_draw",
            backend=backend,
            roc_auc=0.0,
            fpr_at_threshold=0.0,
            tpr_at_threshold=0.0,
            threshold=0.5,
            false_positives=0,
            true_positives=0,
            false_negatives=0,
            true_negatives=0,
            n_test=0,
            headline=headline,
            notes=(
                "NEGATIVE: insufficient classes or samples for suite"
                + (f" (attested_arch={attested})" if attested else " (no attested arch)")
            ),
        )
    train_m, test_m = split_by_base_run(bases, holdout_fraction=0.2, seed=seed)
    if y[test_m].sum() == 0 or y[test_m].sum() == test_m.sum():
        return DetectorResult(
            suite=suite.value,
            policy_name=policy.name,
            signal_set="host_observer_realistic_single_draw",
            backend=backend,
            roc_auc=0.0,
            fpr_at_threshold=0.0,
            tpr_at_threshold=0.0,
            threshold=0.5,
            false_positives=0,
            true_positives=0,
            false_negatives=0,
            true_negatives=0,
            n_test=int(test_m.sum()),
            headline=headline,
            notes="NEGATIVE: test fold lacks both classes",
        )
    clf = LogisticRegression(max_iter=2000, random_state=seed, class_weight="balanced")
    clf.fit(x[train_m], y[train_m])
    scores = clf.predict_proba(x[test_m])[:, 1]
    y_test = y[test_m]
    fpr, tpr, _ = roc_curve(y_test, scores)
    roc_auc = float(auc(fpr, tpr)) if len(fpr) > 1 else 0.0
    train_benign = clf.predict_proba(x[train_m])[:, 1][y[train_m] == 0]
    thresh = float(np.percentile(train_benign, 95)) if len(train_benign) else 0.5
    y_hat = (scores >= thresh).astype(int)
    cm = confusion_matrix(y_test, y_hat, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    return DetectorResult(
        suite=suite.value,
        policy_name=policy.name,
        signal_set="host_observer_realistic_single_draw",
        backend=backend,
        roc_auc=roc_auc,
        fpr_at_threshold=fp / max(fp + tn, 1),
        tpr_at_threshold=tp / max(tp + fn, 1),
        threshold=thresh,
        false_positives=int(fp),
        true_positives=int(tp),
        false_negatives=int(fn),
        true_negatives=int(tn),
        n_test=int(test_m.sum()),
        headline=headline,
        notes="PRELIMINARY — not for external claims until >=8 physical architectures collected",
    )


def run_detector_evaluation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    eval_seed: int = 42,
) -> dict:
    expanded = expand_observations(
        runs, observations_per_base=40, global_seed=eval_seed, single_draw_only=True
    )
    physical = len({lb.base_run_id for _, lb in runs})
    n_arch = len({lb.architecture_id or lb.model_class for _, lb in runs})
    attested_arch = _resolve_attested_architecture(runs, HARD_DETECTOR_POLICY)

    trivial = _eval_suite(
        expanded,
        ViolationSuite.TRIVIAL_MODE,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed,
        headline=False,
    )
    hard_arch = _eval_suite(
        expanded,
        ViolationSuite.HARD_WRONG_ARCH,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 1,
        headline=True,
        attested_arch=attested_arch,
    )
    hard_mod = _eval_suite(
        expanded,
        ViolationSuite.HARD_COVERT_MOD,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 2,
        headline=True,
        attested_arch=attested_arch,
    )

    return {
        "preliminary": True,
        "preliminary_caveats_doc": "docs/PRELIMINARY_CAVEATS.md",
        "backend": backend,
        "physical_base_captures": physical,
        "attested_architecture_resolved": attested_arch,
        "volume_matched_train_profile": {
            "batch_size": HARD_CASE_TRAIN_BS,
            "seq_length": HARD_CASE_TRAIN_SL,
        },
        "distinct_architecture_ids_in_corpus": n_arch,
        "target_architectures": [a[0] for a in ARCHITECTURE_SPECS],
        "min_architectures_for_fingerprint": MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
        "headline_detector_metric": "hard_unauthorized_architecture + hard_covert_modulator",
        "not_headline": "trivial_mode_change (volume/mode only)",
        "suites": {
            "trivial_mode_change": trivial.to_dict(),
            "hard_unauthorized_architecture": hard_arch.to_dict(),
            "hard_covert_modulator": hard_mod.to_dict(),
        },
        "tier_red_note": "covert_modulator.py implements measurement transform; not published as exploit",
    }
