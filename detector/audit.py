"""Detector vs inference consistency audit — volume match, leakage, feature overlap."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import HARD_CASE_TRAIN_BS, HARD_CASE_TRAIN_SL

# Indices in host_observer_feature_vector (see host_observer.py)
FEAT_N_EVENTS = 0
FEAT_TOTAL_BYTES = 1
FEAT_BYTES_PER_S = 2


@dataclass
class FeatureDistribution:
    name: str
    benign_mean: float
    benign_std: float
    violation_mean: float
    violation_std: float
    ks_gap: float


def _volume_matched_train(labels: RunLabels) -> bool:
    return (
        labels.mode == "train"
        and labels.batch_size == HARD_CASE_TRAIN_BS
        and labels.seq_length == HARD_CASE_TRAIN_SL
    )


def _row_features(events: list[TransferEvent], labels: RunLabels, rng) -> np.ndarray:
    from pipeline.features.realistic_observer import apply_realistic_observer

    host = project_host_observer(events)
    obs = apply_realistic_observer(host, rng)
    return host_observer_feature_vector(obs)


def feature_distribution_audit(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    attested_arch: str,
    seed: int = 42,
) -> dict:
    """Compare benign vs wrong-arch rows at matched batch/seq (volume-matched train)."""
    rng = np.random.default_rng(seed)
    benign_feats: list[np.ndarray] = []
    viol_feats: list[np.ndarray] = []
    for events, lb in runs:
        if lb.observation_idx != 0 or not _volume_matched_train(lb):
            continue
        arch = lb.architecture_id or lb.model_class
        x = _row_features(events, lb, rng)
        if arch == attested_arch:
            benign_feats.append(x)
        else:
            viol_feats.append(x)
    if not benign_feats or not viol_feats:
        return {"status": "insufficient_rows", "n_benign": len(benign_feats), "n_violation": len(viol_feats)}
    b = np.vstack(benign_feats)
    v = np.vstack(viol_feats)
    names = ["n_events", "total_bytes", "bytes_per_sec"]
    idxs = [FEAT_N_EVENTS, FEAT_TOTAL_BYTES, FEAT_BYTES_PER_S]
    dists = []
    rel_gaps = []
    for name, j in zip(names, idxs):
        bm, vm = float(np.mean(b[:, j])), float(np.mean(v[:, j]))
        gap = abs(bm - vm)
        rel = gap / max(bm, vm, 1.0)
        rel_gaps.append(rel)
        dists.append(
            asdict(
                FeatureDistribution(
                    name=name,
                    benign_mean=bm,
                    benign_std=float(np.std(b[:, j])),
                    violation_mean=vm,
                    violation_std=float(np.std(v[:, j])),
                    ks_gap=gap,
                )
            )
        )
    # Normalized L2 on full feature vector (scale-invariant)
    b_mean = np.mean(b, axis=0)
    v_mean = np.mean(v, axis=0)
    scale = np.maximum(np.maximum(np.abs(b_mean), np.abs(v_mean)), 1.0)
    full_l2_norm = float(np.linalg.norm((b_mean - v_mean) / scale))
    volume_matched = all(r < 0.10 for r in rel_gaps[:2])
    compute_confound = rel_gaps[1] >= 0.10 if len(rel_gaps) > 1 else False
    return {
        "status": "ok",
        "n_benign": len(benign_feats),
        "n_violation": len(viol_feats),
        "volume_matched_on_coarse_features": volume_matched,
        "compute_volume_confound_at_matched_bs_seq": compute_confound,
        "relative_gap_total_bytes": rel_gaps[1] if len(rel_gaps) > 1 else None,
        "mean_feature_l2_normalized": full_l2_norm,
        "distributions": dists,
        "interpretation": (
            "At fixed (mode, bs, seq), wrong-architecture rows still differ in total_bytes "
            "because model hidden/layers change transfer volume. Binary detector can separate "
            "attested vs other arch using this compute-volume proxy; 12-way inference fails "
            "under realistic noise. NOT a pure policy violation at identical byte volume."
            if compute_confound
            else (
                "Coarse volume features match; binary separation likely uses fine timing/size "
                "structure. 12-way multiclass remains hard due to class overlap."
            )
        ),
        "headline_retraction_risk": (
            "PARTIAL — hard_unauthorized_architecture tracks architecture-correlated "
            "transfer volume at matched knobs, not covert policy alone"
            if compute_confound
            else "LOW — coarse volume matched"
        ),
    }


def leakage_audit_covert_pairs() -> dict:
    return {
        "issue": "covert_modulator paired rows must share split_group_id",
        "fix": "split_by_base_run uses base_run_id without ':covert' suffix",
        "status": "fixed_in_eval",
    }


def inconsistency_explanation() -> dict:
    return {
        "inference_task": "12-class architecture_id under realistic single-draw observer",
        "detector_task": "2-class: attested arch vs other arch at identical train volume profile",
        "why_binary_can_exceed_multiclass": (
            "Logistic detector only needs a separating hyperplane between two clouds at "
            "matched volume; multiclass inference requires 12-way separation with heavy "
            "class overlap and label noise. MI and balanced accuracy on 12-way stay near floor."
        ),
        "leakage_checks": [
            "config-grouped train/test split (no config in both folds)",
            "covert benign/violation pairs share physical base_run_id for splitting",
        ],
    }
