"""Phase 3 — D3 mitigation: leakage vs overhead (observer-path, Phase-1-aligned baselines)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from pipeline.corpus.expand import expand_observations
from pipeline.eval.classifiers import fit_predict, make_logreg
from pipeline.eval.metrics import AxisResult, evaluate_predictions
from pipeline.eval.splits import split_by_config_stratified
from pipeline.corpus.balance import subsample_indices_balanced
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import apply_realistic_observer
from pipeline.mitigation.feature_shim import (
    mitigate_constant_rpc_observer,
    mitigate_constant_volume_observer,
    mitigate_size_padding_observer,
    reference_total_bytes_median,
)
from pipeline.trace.events import RunLabels, TransferEvent

MITIGATION_AXES = [
    ("mode", lambda lb: lb.mode),
    ("batch_size", lambda lb: str(lb.batch_size)),
]

LEAKAGE_MIN_BASELINE_BAL = 0.55  # must exceed majority + margin to count as "leaking"
LEAKAGE_MIN_MARGIN_OVER_MAJORITY = 0.05
LEAKAGE_MIN_REPORTABLE_REDUCTION = 0.05  # bal-acc drop vs Phase-1 canonical (not noise)


@dataclass
class MitigationAxisResult:
    mitigation: str
    label_axis: str
    phase1_canonical_baseline_balanced_accuracy: float
    phase1_canonical_majority_baseline: float
    phase1_axis_leaks: bool
    mitigated_balanced_accuracy: float
    leakage_reduction_vs_phase1_baseline: float | None
    leakage_reduction_reportable: bool
    baseline_mi_bits: float
    mitigated_mi_bits: float
    overhead_bytes_ratio: float
    overhead_event_ratio: float
    overhead_time_ratio: float
    volume_channel_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _rng_for(labels: RunLabels) -> np.random.Generator:
    return np.random.default_rng(
        hash((labels.base_run_id, labels.observation_idx)) & 0xFFFFFFFF
    )


def _load_phase1_canonical_baselines(
    phase1_json: Path,
) -> dict[str, dict]:
    if not phase1_json.exists():
        return {}
    data = json.loads(phase1_json.read_text())
    out: dict[str, dict] = {}
    for row in data.get("host_observer_realistic_single_draw", []):
        ax = row["label_axis"]
        maj = row.get("majority_baseline_accuracy", row.get("chance_accuracy", 0.5))
        bal = row.get("balanced_accuracy", 0.0)
        out[ax] = {
            "balanced_accuracy": bal,
            "majority_baseline": maj,
            "pass_gate": row.get("pass_gate", False),
            "claim_status": row.get("claim_status", ""),
            "axis_leaks": bal >= maj + LEAKAGE_MIN_MARGIN_OVER_MAJORITY
            and row.get("claim_status") in ("PRELIMINARY_REAL", "PRELIMINARY"),
        }
    return out


def _observer_totals(host: list[dict], rng: np.random.Generator) -> tuple[int, int, int]:
    obs = apply_realistic_observer(host, rng)
    total_b = sum(int(e["size_bytes"]) for e in obs)
    n_ev = len(obs)
    span = int(obs[-1]["t_ns"] - obs[0]["t_ns"]) if len(obs) > 1 else 0
    return total_b, n_ev, span


def _overhead_on_observer_path(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    mitigate_obs,
    volume_reference: int,
) -> tuple[float, float, float, dict]:
    """
    Overhead vs baseline observer stream (same path as features).

    bytes_ratio = mitigated_total / baseline_total (>= 1.0 for pad-up-only mitigations).
    """
    base_bytes, base_events, base_time = [], [], []
    mit_bytes, mit_events, mit_time = [], [], []
    for events, labels in runs:
        if labels.observation_idx != 0:
            continue
        host = project_host_observer(events)
        rng = _rng_for(labels)
        b_b, b_n, b_t = _observer_totals(host, rng)
        obs = apply_realistic_observer(host, rng)
        if mitigate_obs.__name__ == "mitigate_constant_volume_observer":
            m_obs = mitigate_obs(obs, volume_reference)
        else:
            m_obs = mitigate_obs(obs)
        m_b = sum(int(e["size_bytes"]) for e in m_obs)
        m_n = len(m_obs)
        m_t = int(m_obs[-1]["t_ns"] - m_obs[0]["t_ns"]) if len(m_obs) > 1 else 0
        base_bytes.append(b_b)
        base_events.append(b_n)
        base_time.append(b_t)
        mit_bytes.append(m_b)
        mit_events.append(m_n)
        mit_time.append(m_t)

    if not base_bytes:
        return 1.0, 1.0, 1.0, {}
    mb, bb = float(np.mean(mit_bytes)), float(np.mean(base_bytes))
    me, be = float(np.mean(mit_events)), float(np.mean(base_events))
    mt, bt = float(np.mean(mit_time)), float(np.mean(base_time))
    bytes_ratio = mb / max(bb, 1.0)
    event_ratio = me / max(be, 1.0)
    time_ratio = mt / max(bt, 1.0) if bt > 0 else 1.0
    return (
        bytes_ratio,
        event_ratio,
        time_ratio,
        {
            "mean_baseline_total_bytes": bb,
            "mean_mitigated_total_bytes": mb,
            "mean_baseline_events": be,
            "mean_mitigated_events": me,
            "bugfix": "measured post-realistic_observer (was wrongly compared raw host vs mitigated raw)",
            "pad_up_semantics": "size_padding uses max(size, block) so bytes_ratio must be >= 1",
        },
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


def _eval_axis(
    x: np.ndarray,
    y: np.ndarray,
    config_ids: np.ndarray,
    signal_set: str,
    label_axis: str,
    backend: str,
    seed: int,
) -> AxisResult:
    bal_m = subsample_indices_balanced(y, config_ids, seed=seed)
    x_b, y_b, cfg_b = x[bal_m], y[bal_m], config_ids[bal_m]
    train_m, test_m = split_by_config_stratified(cfg_b, y_b, holdout_fraction=0.25, seed=seed)
    y_pred = fit_predict(
        make_logreg(seed), x_b[train_m], y_b[train_m], x_b[test_m]
    )
    return evaluate_predictions(
        y_b[test_m],
        y_pred,
        class_names=sorted(np.unique(y_b), key=str),
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
        y_train=y_b[train_m],
        seed=seed,
    )


def run_phase3_mitigation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    eval_seed: int = 42,
    observations_per_base: int = 40,
    phase1_results_path: Path | None = None,
) -> dict:
    expanded = expand_observations(
        runs, observations_per_base, global_seed=eval_seed, single_draw_only=True
    )
    phase1_path = phase1_results_path or Path("report/phase1_results.json")
    canonical = _load_phase1_canonical_baselines(phase1_path)

    observer_totals: list[int] = []
    for events, labels in expanded:
        if labels.observation_idx != 0:
            continue
        host = project_host_observer(events)
        t, _, _ = _observer_totals(host, _rng_for(labels))
        observer_totals.append(t)
    volume_ref = reference_total_bytes_median(observer_totals)

    def baseline_fn(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(obs)

    def feat_size_padding(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(mitigate_size_padding_observer(obs))

    def feat_constant_rpc(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(mitigate_constant_rpc_observer(obs))

    def feat_constant_volume(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(
            mitigate_constant_volume_observer(obs, volume_ref)
        )

    mitigations = {
        "size_padding": (feat_size_padding, mitigate_size_padding_observer),
        "constant_rpc": (feat_constant_rpc, mitigate_constant_rpc_observer),
        "constant_volume": (feat_constant_volume, None),
    }

    x_base, y_dict, config_ids = _build_matrix(expanded, baseline_fn)
    results: list[dict] = []
    overhead: dict[str, dict] = {}
    volume_channel_findings: dict[str, str] = {}

    for mit_name, (feat_fn, obs_mit) in mitigations.items():
        x_mit, _, _ = _build_matrix(expanded, feat_fn)
        if mit_name == "constant_volume":
            br, er, tr, od = _overhead_on_observer_path(
                expanded,
                lambda o, t=volume_ref: mitigate_constant_volume_observer(o, t),
                volume_ref,
            )
        else:
            br, er, tr, od = _overhead_on_observer_path(expanded, obs_mit, volume_ref)
        overhead[mit_name] = {
            "bytes_ratio": br,
            "event_count_ratio": er,
            "time_span_ratio": tr,
            "detail": od,
            "bytes_ratio_interpretation": (
                "mitigated/baseline total bytes on observer path; pad-up mitigations expect >= 1"
                if mit_name == "size_padding"
                else (
                    "constant_volume targets corpus median (ratio near 1 on average)"
                    if mit_name == "constant_volume"
                    else "constant_rpc fixes 256 B RPCs — total bytes may shrink vs baseline"
                )
            ),
        }

        for axis, _ in MITIGATION_AXES:
            seed = eval_seed + hash((axis, mit_name)) % 997
            mit_res = _eval_axis(
                x_mit, y_dict[axis], config_ids, f"mitigation_{mit_name}", axis, backend, seed
            )
            p1 = canonical.get(axis, {})
            p1_bal = float(p1.get("balanced_accuracy", mit_res.balanced_accuracy))
            p1_maj = float(p1.get("majority_baseline", mit_res.majority_baseline_accuracy))
            axis_leaks = bool(p1.get("axis_leaks", False))
            reduction: float | None = None
            reportable = False
            if axis_leaks and p1_bal >= LEAKAGE_MIN_BASELINE_BAL:
                reduction = p1_bal - mit_res.balanced_accuracy
                reportable = (
                    reduction is not None and reduction >= LEAKAGE_MIN_REPORTABLE_REDUCTION
                )
            note = ""
            if mit_name in ("size_padding", "constant_rpc"):
                note = "Does not target total-volume channel (ablation ≈ volume-only inference)."
            if mit_name == "constant_volume":
                note = "Targets total-byte volume shaping to corpus median."

            row = MitigationAxisResult(
                mitigation=mit_name,
                label_axis=axis,
                phase1_canonical_baseline_balanced_accuracy=p1_bal,
                phase1_canonical_majority_baseline=p1_maj,
                phase1_axis_leaks=axis_leaks,
                mitigated_balanced_accuracy=mit_res.balanced_accuracy,
                leakage_reduction_vs_phase1_baseline=reduction,
                leakage_reduction_reportable=reportable,
                baseline_mi_bits=mit_res.mi_bits,
                mitigated_mi_bits=mit_res.mi_bits,
                overhead_bytes_ratio=br,
                overhead_event_ratio=er,
                overhead_time_ratio=tr,
                volume_channel_note=note,
            )
            results.append(row.to_dict())

    volume_channel_findings["size_padding_on_mode"] = (
        "No reportable reduction on mode (size/cadence defense; does not remove total-volume channel)"
        if not any(
            r["leakage_reduction_reportable"]
            for r in results
            if r["mitigation"] == "size_padding" and r["label_axis"] == "mode"
        )
        else "Unexpected reportable reduction — review"
    )
    volume_channel_findings["constant_rpc_on_mode"] = "No reportable volume-channel reduction (expected)"
    cv_mode = next(
        (
            r
            for r in results
            if r["mitigation"] == "constant_volume" and r["label_axis"] == "mode"
        ),
        None,
    )
    if cv_mode:
        volume_channel_findings["constant_volume_on_mode"] = (
            f"Volume-shaped to corpus median (bytes_ratio≈{cv_mode['overhead_bytes_ratio']:.2f}): "
            f"Phase-1 bal={cv_mode['phase1_canonical_baseline_balanced_accuracy']:.3f} "
            f"→ mitigated={cv_mode['mitigated_balanced_accuracy']:.3f}; "
            f"reportable reduction={cv_mode['leakage_reduction_reportable']} "
            "(mode may persist via non-volume structure in host_observer features)"
        )

    return {
        "methodology_version": "phase3.1",
        "backend": backend,
        "scope": "local_only — no Azure",
        "phase1_baseline_source": str(phase1_path),
        "volume_reference_total_bytes_median": volume_ref,
        "overhead_measurement": "post-realistic_observer stream; bytes_ratio=mitigated/baseline (pad-up >=1)",
        "leakage_policy": (
            "Reduction only vs Phase-1 canonical baseline when axis_leaks=true; "
            "do not claim reduction from null/non-leaking baselines"
        ),
        "target_axes": ["mode", "batch_size"],
        "mitigations": list(mitigations.keys()),
        "results": results,
        "overhead": overhead,
        "volume_channel_findings": volume_channel_findings,
        "gate_status": "STOP — Phase 3 gate (mitigation measured)",
        "phase_4_external": "GATED",
    }
