"""Phase 2 policy-deviation detector evaluation (preliminary)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc,
    confusion_matrix,
    roc_curve,
)

from detector.policy import AttestedPolicy, DEFAULT_TRAIN_POLICY, violation_label
from pipeline.corpus.expand import expand_observations
from pipeline.eval.splits import split_by_base_run
from pipeline.features.host_observer import project_host_observer
from pipeline.features.realistic_observer import realistic_observer_features
from pipeline.trace.events import RunLabels, TransferEvent


@dataclass
class DetectorResult:
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
    mean_score_violation: float
    mean_score_benign: float
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _features_for_run(
    events: list,
    labels: RunLabels,
) -> np.ndarray:
    host = project_host_observer(events)
    rng = np.random.default_rng(
        hash((labels.base_run_id, labels.observation_idx)) & 0xFFFFFFFF
    )
    return realistic_observer_features(host, rng)


def run_detector_evaluation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    policy: AttestedPolicy | None = None,
    eval_seed: int = 42,
    *,
    single_draw: bool = True,
) -> dict:
    """
    Train binary detector: in-policy vs deviation on realistic host-observer features.
    PRELIMINARY — same corpus caveats as Phase 1.
    """
    policy = policy or DEFAULT_TRAIN_POLICY
    expanded = expand_observations(
        runs, observations_per_base=40, global_seed=eval_seed, single_draw_only=single_draw
    )

    xs: list[np.ndarray] = []
    ys: list[int] = []
    base_ids: list[str] = []
    for events, labels in expanded:
        if single_draw and labels.observation_idx != 0:
            continue
        xs.append(_features_for_run(events, labels))
        ys.append(violation_label(labels, policy))
        base_ids.append(labels.base_run_id)

    x = np.vstack(xs)
    y = np.array(ys)
    base_arr = np.array(base_ids)

    if len(np.unique(y)) < 2:
        return {
            "preliminary": True,
            "policy": policy.name,
            "backend": backend,
            "notes": "NEGATIVE: only one policy class in corpus",
            "detector": DetectorResult(
                policy.name,
                "host_observer_realistic_single_draw",
                backend,
                0.0,
                0.0,
                0.0,
                0.5,
                0,
                0,
                0,
                int(len(y)),
                0.0,
                0.0,
                notes="single class",
            ).to_dict(),
        }

    train_m, test_m = split_by_base_run(base_arr, holdout_fraction=0.2, seed=eval_seed)
    clf = LogisticRegression(max_iter=2000, random_state=eval_seed, class_weight="balanced")
    clf.fit(x[train_m], y[train_m])
    scores = clf.predict_proba(x[test_m])[:, 1]
    y_test = y[test_m]

    fpr, tpr, thresholds = roc_curve(y_test, scores)
    roc_auc = float(auc(fpr, tpr)) if len(fpr) > 1 else 0.0

    # Operating point: threshold at 95th percentile of benign train scores
    train_scores = clf.predict_proba(x[train_m])[:, 1]
    train_benign = train_scores[y[train_m] == 0]
    thresh = float(np.percentile(train_benign, 95)) if len(train_benign) else 0.5
    y_hat = (scores >= thresh).astype(int)

    cm = confusion_matrix(y_test, y_hat, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    fpr_op = fp / max(fp + tn, 1)
    tpr_op = tp / max(tp + fn, 1)

    # FP budget proxy: FP per 24h per node (assume test window = 1 unit)
    fp_per_day = float(fp)

    by_type: dict[str, int] = {}
    for events, labels in expanded:
        if labels.base_run_id not in set(base_arr[test_m]):
            continue
        if single_draw and labels.observation_idx != 0:
            continue
        key = f"{labels.mode}:{labels.architecture_id or labels.model_class}"
        if violation_label(labels, policy) == 1:
            by_type[key] = by_type.get(key, 0) + 1

    det = DetectorResult(
        policy_name=policy.name,
        signal_set="host_observer_realistic_single_draw",
        backend=backend,
        roc_auc=roc_auc,
        fpr_at_threshold=fpr_op,
        tpr_at_threshold=tpr_op,
        threshold=thresh,
        false_positives=int(fp),
        true_positives=int(tp),
        false_negatives=int(fn),
        true_negatives=int(tn),
        n_test=int(test_m.sum()),
        mean_score_violation=float(np.mean(scores[y_test == 1])) if np.any(y_test == 1) else 0.0,
        mean_score_benign=float(np.mean(scores[y_test == 0])) if np.any(y_test == 0) else 0.0,
        notes="PRELIMINARY; see docs/PRELIMINARY_CAVEATS.md",
    )

    return {
        "preliminary": True,
        "preliminary_caveats_doc": "docs/PRELIMINARY_CAVEATS.md",
        "policy": policy.name,
        "backend": backend,
        "physical_base_captures": len(set(base_ids)),
        "detector": det.to_dict(),
        "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "false_positives_per_test_window": fp_per_day,
        "violation_types_in_test": by_type,
        "tier_red_modulator": "not_in_repo (private); violations from cross-mode/architecture traces",
    }
