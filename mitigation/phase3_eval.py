"""Phase 3 — D3 mitigation: leakage reduction on mode/batch_size vs overhead."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from pipeline.corpus.expand import expand_observations
from pipeline.eval.classifiers import fit_predict, make_logreg
from pipeline.eval.metrics import AxisResult, evaluate_predictions
from pipeline.eval.splits import split_by_config_stratified
from pipeline.corpus.balance import subsample_indices_balanced
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import apply_realistic_observer
from pipeline.mitigation.feature_shim import mitigate_constant_rpc, mitigate_size_padding
from pipeline.trace.events import RunLabels, TransferEvent

MITIGATION_AXES = [
    ("mode", lambda lb: lb.mode),
    ("batch_size", lambda lb: str(lb.batch_size)),
]


@dataclass
class MitigationAxisResult:
    mitigation: str
    label_axis: str
    baseline_balanced_accuracy: float
    mitigated_balanced_accuracy: float
    baseline_mi_bits: float
    mitigated_mi_bits: float
    leakage_reduction_balanced: float
    overhead_bytes_ratio: float
    overhead_event_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def _rng_for(labels: RunLabels) -> np.random.Generator:
    return np.random.default_rng(
        hash((labels.base_run_id, labels.observation_idx)) & 0xFFFFFFFF
    )


def _build_matrix(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    rows = []
    for events, labels in runs:
        if labels.observation_idx != 0:
            continue
        host = project_host_observer(events)
        rows.append(
            (
                feature_fn(host, _rng_for(labels)),
                labels,
                labels.config_id or labels.workload_id,
            )
        )
    x = np.vstack([r[0] for r in rows])
    y_dict = {ax: np.array([fn(r[1]) for r in rows]) for ax, fn in MITIGATION_AXES}
    config_ids = np.array([r[2] for r in rows])
    return x, y_dict, config_ids


def _overhead_stats(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    mitigated_fn,
) -> tuple[float, float]:
    base_bytes, mit_bytes, base_n, mit_n = [], [], [], []
    for events, labels in runs:
        if labels.observation_idx != 0:
            continue
        host = project_host_observer(events)
        base_bytes.append(sum(e["size_bytes"] for e in host))
        base_n.append(len(host))
        mit = mitigated_fn(host)
        mit_bytes.append(sum(e["size_bytes"] for e in mit))
        mit_n.append(len(mit))
    if not base_bytes:
        return 1.0, 1.0
    return float(np.mean(mit_bytes) / max(np.mean(base_bytes), 1)), float(
        np.mean(mit_n) / max(np.mean(base_n), 1)
    )


def _eval_axis_mitigation(
    x: np.ndarray,
    y: np.ndarray,
    config_ids: np.ndarray,
    mitigation_name: str,
    label_axis: str,
    backend: str,
    seed: int,
) -> AxisResult:
    bal_m = subsample_indices_balanced(y, config_ids, seed=seed)
    x_b, y_b, cfg_b = x[bal_m], y[bal_m], config_ids[bal_m]
    train_m, test_m = split_by_config_stratified(cfg_b, y_b, holdout_fraction=0.25, seed=seed)
    y_train, y_test = y_b[train_m], y_b[test_m]
    y_pred = fit_predict(make_logreg(seed), x_b[train_m], y_train, x_b[test_m])
    res = evaluate_predictions(
        y_test,
        y_pred,
        class_names=sorted(np.unique(y_b), key=str),
        label_axis=label_axis,
        signal_set=f"mitigation_{mitigation_name}",
        backend=backend,
        y_train=y_train,
        seed=seed,
    )
    return res


def run_phase3_mitigation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    eval_seed: int = 42,
    observations_per_base: int = 40,
) -> dict:
    expanded = expand_observations(
        runs, observations_per_base, global_seed=eval_seed, single_draw_only=True
    )

    def baseline_fn(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(obs)

    mitigations = {
        "size_padding": lambda host, rng: host_observer_feature_vector(
            mitigate_size_padding(apply_realistic_observer(host, rng))
        ),
        "constant_rpc": lambda host, rng: host_observer_feature_vector(
            mitigate_constant_rpc(apply_realistic_observer(host, rng))
        ),
    }

    x_base, y_dict, config_ids = _build_matrix(expanded, baseline_fn)
    results: list[dict] = []
    overhead: dict[str, dict] = {}

    for mit_name, mit_fn in mitigations.items():
        x_mit, _, _ = _build_matrix(expanded, mit_fn)
        br, er = _overhead_stats(
            expanded,
            lambda h: mitigate_size_padding(h)
            if mit_name == "size_padding"
            else mitigate_constant_rpc(h),
        )
        overhead[mit_name] = {
            "bytes_ratio": br,
            "event_count_ratio": er,
        }
        for axis, _ in MITIGATION_AXES:
            y = y_dict[axis]
            base_res = _eval_axis_mitigation(
                x_base, y, config_ids, "baseline", axis, backend, eval_seed + hash(axis) % 997
            )
            mit_res = _eval_axis_mitigation(
                x_mit, y, config_ids, mit_name, axis, backend, eval_seed + hash(axis + mit_name) % 997
            )
            row = MitigationAxisResult(
                mitigation=mit_name,
                label_axis=axis,
                baseline_balanced_accuracy=base_res.balanced_accuracy,
                mitigated_balanced_accuracy=mit_res.balanced_accuracy,
                baseline_mi_bits=base_res.mi_bits,
                mitigated_mi_bits=mit_res.mi_bits,
                leakage_reduction_balanced=base_res.balanced_accuracy
                - mit_res.balanced_accuracy,
                overhead_bytes_ratio=br,
                overhead_event_ratio=er,
            )
            results.append(row.to_dict())

    return {
        "methodology_version": "phase3.0",
        "backend": backend,
        "scope": "local_only — no Azure",
        "external_claims": "Azure Phase 4 gated; mitigation numbers PRELIMINARY until independent replay",
        "target_axes": ["mode", "batch_size"],
        "mitigations": list(mitigations.keys()),
        "results": results,
        "overhead": overhead,
        "gate_status": "STOP — Phase 3 gate (mitigation measured)",
    }
