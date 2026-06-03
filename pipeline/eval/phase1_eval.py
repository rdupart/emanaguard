"""Phase 1 evaluation — realistic host observer, ablations, learning curves, D3 preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from pipeline.corpus.expand import corpus_statistics, expand_observations
from pipeline.eval.classifiers import fit_predict, make_logreg, make_rf
from pipeline.eval.metrics import AxisResult, evaluate_predictions
from pipeline.eval.splits import split_by_base_run, split_by_config
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import (
    apply_realistic_observer,
    realistic_observer_features,
    volume_only_features,
)
from pipeline.features.vm_ground_truth import vm_ground_truth_feature_vector
from pipeline.mitigation.feature_shim import mitigate_constant_rpc, mitigate_size_padding
from pipeline.trace.events import RunLabels, TransferEvent

LABEL_AXES = [
    ("mode", lambda lb: lb.mode),
    ("model_class", lambda lb: lb.model_class),
    ("batch_size", lambda lb: str(lb.batch_size)),
    ("seq_length", lambda lb: str(lb.seq_length)),
    ("llm_phase", lambda lb: lb.llm_phase),
]


@dataclass
class LearningCurvePoint:
    label_axis: str
    n_train_base_runs: int
    n_train_samples: int
    accuracy: float
    ci_lower: float
    ci_upper: float
    chance_accuracy: float


def _rng_for(labels: RunLabels) -> np.random.Generator:
    key = hash((labels.base_run_id, labels.observation_idx)) & 0xFFFFFFFF
    return np.random.default_rng(key)


def _collapse_runs_to_base_means(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn: Callable[[list[dict], np.random.Generator], np.ndarray],
) -> list[tuple[np.ndarray, RunLabels, str]]:
    """One training row per base capture: mean over stochastic observer samples."""
    from collections import defaultdict

    buckets: dict[str, dict] = defaultdict(lambda: {"feats": [], "labels": None})
    for events, labels in runs:
        host = project_host_observer(events)
        buckets[labels.base_run_id]["feats"].append(feature_fn(host, _rng_for(labels)))
        buckets[labels.base_run_id]["labels"] = labels
    out: list[tuple[np.ndarray, RunLabels, str]] = []
    for base_id, data in buckets.items():
        mean_f = np.mean(data["feats"], axis=0)
        lb = data["labels"]
        cid = lb.config_id or lb.workload_id
        out.append((mean_f, lb, cid))
    return out


def _build_matrix(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn: Callable[[list[dict], np.random.Generator], np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    collapsed = _collapse_runs_to_base_means(runs, feature_fn)
    xs = np.vstack([c[0] for c in collapsed])
    base_ids = np.array([c[1].base_run_id for c in collapsed])
    config_ids = np.array([c[2] for c in collapsed])
    ys: dict[str, np.ndarray] = {ax: np.array([fn(c[1]) for c in collapsed]) for ax, fn in LABEL_AXES}
    return xs, base_ids, config_ids, ys


def _eval_axis_masked(
    x: np.ndarray,
    y: np.ndarray,
    train_m: np.ndarray,
    test_m: np.ndarray,
    label_axis: str,
    signal_set: str,
    backend: str,
    clf_factory,
    seed: int,
) -> AxisResult:
    classes = np.unique(y)
    if len(classes) < 2:
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y)),
            n_classes=len(classes),
            chance_accuracy=1.0,
            accuracy=0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            confusion=[[int(len(y))]] if len(y) else [[]],
            class_names=[str(c) for c in classes],
            notes="NEGATIVE: single class",
        )
    if train_m.sum() < 4 or test_m.sum() < 2:
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y)),
            n_classes=len(classes),
            chance_accuracy=1.0 / len(classes),
            accuracy=0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            confusion=[],
            class_names=[str(c) for c in classes],
            notes="insufficient train/test after grouped split",
        )
    y_pred = fit_predict(
        clf_factory(seed), x[train_m], y[train_m], x[test_m]
    )
    return evaluate_predictions(
        y[test_m],
        y_pred,
        class_names=[str(c) for c in classes],
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
    )


def _learning_curves(
    x: np.ndarray,
    y: np.ndarray,
    base_ids: np.ndarray,
    config_ids: np.ndarray,
    train_m_full: np.ndarray,
    label_axis: str,
    signal_set: str,
    backend: str,
    seed: int,
    fractions: list[float] | None = None,
) -> list[LearningCurvePoint]:
    fractions = fractions or [0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0]
    train_configs = list(set(config_ids[train_m_full]))
    rng_lc = np.random.default_rng(seed + hash(label_axis) % 10000)
    rng_lc.shuffle(train_configs)
    test_m = ~train_m_full
    points: list[LearningCurvePoint] = []
    for frac in fractions:
        n_c = max(2, int(len(train_configs) * frac))
        use = set(train_configs[:n_c])
        sub_train = train_m_full & np.isin(config_ids, list(use))
        if sub_train.sum() < 4 or len(np.unique(y[sub_train])) < 2:
            continue
        if len(np.unique(y[test_m])) < 2:
            continue
        res = _eval_axis_masked(
            x, y, sub_train, test_m, label_axis, signal_set, backend, make_logreg, seed
        )
        points.append(
            LearningCurvePoint(
                label_axis=label_axis,
                n_train_base_runs=n_c,
                n_train_samples=int(sub_train.sum()),
                accuracy=res.accuracy,
                ci_lower=res.ci_lower,
                ci_upper=res.ci_upper,
                chance_accuracy=res.chance_accuracy,
            )
        )
    return points


def _eval_all_axes(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn: Callable[[list[dict], np.random.Generator], np.ndarray],
    signal_set: str,
    backend: str,
    seed: int,
) -> tuple[list[AxisResult], list[dict], list[LearningCurvePoint]]:
    x, base_ids, config_ids, y_dict = _build_matrix(runs, feature_fn)
    train_m, test_m = split_by_config(config_ids, holdout_fraction=0.25, seed=seed)
    results: list[AxisResult] = []
    curves: list[LearningCurvePoint] = []
    for axis, _ in LABEL_AXES:
        y = y_dict[axis]
        results.append(
            _eval_axis_masked(
                x, y, train_m, test_m, axis, signal_set, backend, make_logreg, seed
            )
        )
        curves.extend(
            _learning_curves(
                x, y, base_ids, config_ids, train_m, axis, signal_set, backend, seed
            )
        )
    curve_dicts = [asdict(c) for c in curves]
    return results, curve_dicts, curves


def _mitigation_eval(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    seed: int,
) -> dict[str, list[dict]]:
    """D3 preview on realistic observer event streams."""

    def feats_padded(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(mitigate_size_padding(obs))

    def feats_const_rpc(host, rng):
        obs = apply_realistic_observer(host, rng)
        return host_observer_feature_vector(mitigate_constant_rpc(obs))

    out: dict[str, list[dict]] = {}
    for name, fn in [
        ("mitigation_size_padding", feats_padded),
        ("mitigation_constant_rpc", feats_const_rpc),
    ]:
        res, _, _ = _eval_all_axes(runs, fn, name, backend, seed)
        out[name] = [r.to_dict() for r in res]
    return out


def run_evaluation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    seeds: list[int] | None = None,
    eval_seed: int = 42,
    observations_per_base: int = 40,
) -> dict:
    """
    Full Phase 1.2 evaluation on local-gpu captures + scaled stochastic observations.
    """
    expanded = expand_observations(runs, observations_per_base, global_seed=eval_seed)
    stats = corpus_statistics(expanded)

    def realistic_fn(host, rng):
        return realistic_observer_features(host, rng)

    def idealized_fn(host, rng):
        return host_observer_feature_vector(host)

    def volume_fn(host, rng):
        return volume_only_features(host, rng)

    headline, learning_curves, _ = _eval_all_axes(
        expanded, realistic_fn, "host_observer_realistic", backend, eval_seed
    )

    idealized, _, _ = _eval_all_axes(
        expanded, idealized_fn, "host_observer_idealized_upper_bound", backend, eval_seed
    )

    ablation_volume, _, _ = _eval_all_axes(
        expanded, volume_fn, "ablation_volume_only", backend, eval_seed
    )

    from collections import defaultdict

    vm_buckets: dict[str, list] = defaultdict(list)
    lb_map: dict[str, RunLabels] = {}
    for events, labels in runs:
        vm_buckets[labels.base_run_id].append(vm_ground_truth_feature_vector(events))
        lb_map[labels.base_run_id] = labels
    vm_collapsed = []
    config_vm = []
    for base_id, feats in vm_buckets.items():
        vm_collapsed.append(np.mean(feats, axis=0))
        config_vm.append(lb_map[base_id].config_id or lb_map[base_id].workload_id)
    x_vm = np.vstack(vm_collapsed)
    y_vm = {
        ax: np.array([fn(lb_map[b]) for b in vm_buckets])
        for ax, fn in LABEL_AXES
    }
    train_m, test_m = split_by_config(np.array(config_vm), holdout_fraction=0.25, seed=eval_seed)
    vm_results = []
    for axis, _ in LABEL_AXES:
        vm_results.append(
            _eval_axis_masked(
                x_vm,
                y_vm[axis],
                train_m,
                test_m,
                axis,
                "vm_ground_truth",
                backend,
                make_rf,
                eval_seed,
            )
        )

    mitigation = _mitigation_eval(expanded, backend, eval_seed)

    # Interpret ablation: if volume-only ≈ realistic, channel is coarse
    ablation_notes = {}
    for h, v in zip(headline, ablation_volume):
        if h.label_axis != v.label_axis:
            continue
        if v.accuracy >= 0.9 and abs(h.accuracy - v.accuracy) < 0.05:
            ablation_notes[h.label_axis] = (
                "Coarse volume leakage: total-bytes ablation within 5% of full realistic features."
            )
        elif v.accuracy >= 0.85 and h.accuracy < v.accuracy + 0.1:
            ablation_notes[h.label_axis] = (
                "Volume channel dominates; fine-grained claim not supported."
            )

    return {
        "backend": backend,
        "methodology_version": "phase1.2",
        "corpus_statistics": stats,
        "observations_per_base_capture": observations_per_base,
        "headline_signal_set": "host_observer_realistic",
        "host_observer_realistic": [r.to_dict() for r in headline],
        "host_observer_idealized": [r.to_dict() for r in idealized],
        "ablation_volume_only": [r.to_dict() for r in ablation_volume],
        "ablation_interpretation": ablation_notes,
        "vm_ground_truth": [r.to_dict() for r in vm_results],
        "learning_curves": learning_curves,
        "mitigation_preview_d3": mitigation,
        "observer_transform_doc": "pipeline/features/realistic_observer.py",
        "split_policy": "hold out 25% of config_id groups; ML uses one mean feature vector per base capture (40 obs averaged)",
        "classifier_samples": stats.get("unique_base_captures", 0),
    }


# Legacy bundle for smoke tests
@dataclass
class EvalBundle:
    backend: str
    vm_results: list
    host_results: list
    host_sequence_results: list

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "vm_ground_truth": [r.to_dict() for r in self.vm_results],
            "host_observer": [r.to_dict() for r in self.host_results],
            "host_observer_sequence": [r.to_dict() for r in self.host_sequence_results],
        }
