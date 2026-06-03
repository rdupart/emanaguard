"""Phase 1 evaluation — realistic host observer, ablations, learning curves, D3 preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from pipeline.corpus.expand import corpus_statistics, expand_observations
from pipeline.eval.classifiers import fit_predict, make_logreg, make_rf
from pipeline.corpus.balance import label_counts_physical, subsample_indices_balanced
from pipeline.eval.metrics import (
    MI_PASS_FLOOR_BITS,
    AxisResult,
    chance_level,
    evaluate_predictions,
    majority_baseline,
)

NULL_CLAIM_AXES = frozenset({"seq_length", "llm_phase"})
PRELIMINARY_REAL_AXES = frozenset({"mode", "batch_size"})
from pipeline.eval.splits import split_by_config_stratified, split_holdout_architectures
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import (
    apply_realistic_observer,
    realistic_observer_features,
    volume_only_features,
)
from pipeline.features.vm_ground_truth import vm_ground_truth_feature_vector
from pipeline.mitigation.feature_shim import mitigate_constant_rpc, mitigate_size_padding
from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import (
    MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
    all_architecture_ids,
    count_architectures_in_runs,
)

LABEL_AXES = [
    ("mode", lambda lb: lb.mode),
    ("model_class", lambda lb: lb.model_class),
    ("architecture_id", lambda lb: lb.architecture_id or lb.model_class),
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
    *,
    aggregation: str = "mean_per_base",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    if aggregation == "mean_per_base":
        collapsed = _collapse_runs_to_base_means(runs, feature_fn)
        rows = [(c[0], c[1], c[2]) for c in collapsed]
    elif aggregation == "single_draw":
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
    else:
        raise ValueError(aggregation)

    xs = np.vstack([r[0] for r in rows])
    base_ids = np.array([r[1].base_run_id for r in rows])
    config_ids = np.array([r[2] for r in rows])
    arch_ids = np.array([r[1].architecture_id or r[1].model_class for r in rows])
    ys = {ax: np.array([fn(r[1]) for r in rows]) for ax, fn in LABEL_AXES}
    return xs, base_ids, config_ids, arch_ids, ys


def _eval_all_axes_with_matrix(
    aggregation: str,
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn: Callable,
    signal_set: str,
    backend: str,
    seed: int,
) -> tuple[list[AxisResult], list[dict]]:
    x, base_ids, config_ids, _arch, y_dict = _build_matrix(
        runs, feature_fn, aggregation=aggregation
    )
    results: list[AxisResult] = []
    curves: list[dict] = []
    for axis, fn in LABEL_AXES:
        y = y_dict[axis]
        bal_m = subsample_indices_balanced(y, config_ids, seed=seed + hash(axis) % 997)
        x_b, y_b, cfg_b = x[bal_m], y[bal_m], config_ids[bal_m]
        train_m, test_m = split_by_config_stratified(
            cfg_b, y_b, holdout_fraction=0.25, seed=seed + hash(axis) % 997
        )
        results.append(
            _eval_axis_masked(
                x_b, y_b, train_m, test_m, axis, signal_set, backend, make_logreg, seed
            )
        )
    return results, curves


def eval_held_out_architecture(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    feature_fn: Callable,
    backend: str,
    seed: int,
    aggregation: str = "single_draw",
) -> dict:
    """Generalization to entirely unseen architecture_id in test (not unseen runs only)."""
    expanded = runs  # caller passes already expanded
    x, _b, _c, arch_ids, y_dict = _build_matrix(
        expanded, feature_fn, aggregation=aggregation
    )
    n_arch_corpus = len(set(arch_ids))
    train_m, test_m, held_out = split_holdout_architectures(
        arch_ids, holdout_fraction=0.25, seed=seed, min_train_architectures=2
    )
    train_archs = sorted(set(arch_ids[train_m]))
    test_archs = sorted(set(arch_ids[test_m]))
    out: dict = {
        "held_out_architectures": held_out,
        "train_architectures": train_archs,
        "test_architectures": test_archs,
        "distinct_architectures_in_physical_corpus": n_arch_corpus,
        "min_architectures_for_valid_fingerprint_claim": MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
        "split": (
            "entire architecture_id held out of train; test rows are only unseen "
            "architectures (single-draw realistic observer)"
        ),
        "aggregation": aggregation,
        "headline_axis": "architecture_id",
        "model_class_status": "RETRACTED — confounded with volume/mode; not a fingerprint axis",
        "axes": {},
    }
    if n_arch_corpus < MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM:
        out["gate_status"] = (
            f"BLOCKED: only {n_arch_corpus} physical architectures; need "
            f">={MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM} after collect on expanded corpus"
        )
    elif len(train_archs) < 2:
        out["gate_status"] = "NEGATIVE: train fold has fewer than 2 architecture classes"
    else:
        out["gate_status"] = "PRELIMINARY — interpret held-out accuracy; no external fingerprint claim until PASS"

    for axis in ("architecture_id", "model_class"):
        y = y_dict[axis]
        res = _eval_axis_masked(
            x,
            y,
            train_m,
            test_m,
            axis,
            "host_observer_realistic_held_out_model",
            backend,
            make_logreg,
            seed,
        )
        if axis == "model_class":
            res.pass_lower_ci_above_chance = False
            res.notes = (
                (res.notes or "")
                + " RETRACTED: model_class not reported as fingerprint result"
            ).strip()
        elif n_arch_corpus < MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM:
            res.pass_lower_ci_above_chance = False
            res.notes = (
                (res.notes or "")
                + f" RETRACTED: <{MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM} architectures in corpus"
            ).strip()
        elif axis == "architecture_id" and not res.pass_lower_ci_above_chance:
            res.notes = (
                (res.notes or "")
                + " NEGATIVE: held-out-model does not generalize — honest bounding result"
            ).strip()
        out["axes"][axis] = res.to_dict()
    return out


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
    y = np.asarray(y)
    all_labels = sorted(np.unique(y), key=str)
    y_train, y_test = y[train_m], y[test_m]

    uni = chance_level(len(all_labels))
    maj = majority_baseline(y_train) if train_m.sum() else uni

    def _empty(notes: str, n_test: int = 0) -> AxisResult:
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=n_test,
            n_classes=len(all_labels),
            chance_accuracy=maj,
            majority_baseline_accuracy=maj,
            uniform_chance_accuracy=uni,
            accuracy=0.0,
            balanced_accuracy=0.0,
            macro_f1=0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            balanced_ci_lower=0.0,
            balanced_ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            pass_balanced_beat_majority=False,
            pass_mi_above_floor=False,
            pass_gate=False,
            confusion=[],
            class_names=[str(c) for c in all_labels],
            notes=notes,
        )

    if len(all_labels) < 2:
        return _empty("NEGATIVE: corpus has a single class for this axis", int(len(y)))
    if train_m.sum() < 4 or test_m.sum() < 2:
        return _empty("insufficient train/test after grouped split", int(test_m.sum()))
    if len(np.unique(y_train)) < 2:
        return _empty("NEGATIVE: train fold has a single class", int(test_m.sum()))
    if len(np.unique(y_test)) < 2:
        return _empty(
            "NEGATIVE: test fold has a single class (holdout did not include all label values)",
            int(test_m.sum()),
        )

    y_pred = fit_predict(
        clf_factory(seed), x[train_m], y_train, x[test_m]
    )
    return evaluate_predictions(
        y_test,
        y_pred,
        class_names=all_labels,
        all_labels=all_labels,
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
        y_train=y_train,
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
    x, base_ids, config_ids, _arch, y_dict = _build_matrix(
        runs, feature_fn, aggregation="mean_per_base"
    )
    results: list[AxisResult] = []
    curves: list[LearningCurvePoint] = []
    for axis, fn in LABEL_AXES:
        y = y_dict[axis]
        bal_m = subsample_indices_balanced(y, config_ids, seed=seed + hash(axis) % 997)
        x_b, y_b, cfg_b, base_b = x[bal_m], y[bal_m], config_ids[bal_m], base_ids[bal_m]
        train_m, test_m = split_by_config_stratified(
            cfg_b, y_b, holdout_fraction=0.25, seed=seed + hash(axis) % 997
        )
        results.append(
            _eval_axis_masked(
                x_b, y_b, train_m, test_m, axis, signal_set, backend, make_logreg, seed
            )
        )
        curves.extend(
            _learning_curves(
                x_b, y_b, base_b, cfg_b, train_m, axis, signal_set, backend, seed
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
    expanded_mean = expand_observations(
        runs, observations_per_base, global_seed=eval_seed
    )
    expanded_single = expand_observations(
        runs, observations_per_base, global_seed=eval_seed, single_draw_only=True
    )
    stats = corpus_statistics(
        expanded_mean, observations_per_base=observations_per_base
    )
    stats_single = corpus_statistics(
        expanded_single, observations_per_base=1, single_draw=True
    )

    def realistic_fn(host, rng):
        return realistic_observer_features(host, rng)

    def idealized_fn(host, rng):
        return host_observer_feature_vector(host)

    def volume_fn(host, rng):
        return volume_only_features(host, rng)

    headline_mean, learning_curves, _ = _eval_all_axes(
        expanded_mean, realistic_fn, "host_observer_realistic_mean_draw", backend, eval_seed
    )
    headline_single, _ = _eval_all_axes_with_matrix(
        "single_draw",
        expanded_single,
        realistic_fn,
        "host_observer_realistic_single_draw",
        backend,
        eval_seed,
    )
    held_out_model = eval_held_out_architecture(
        expanded_single, realistic_fn, backend, eval_seed, aggregation="single_draw"
    )

    idealized, _, _ = _eval_all_axes(
        expanded_mean, idealized_fn, "host_observer_idealized_upper_bound", backend, eval_seed
    )

    ablation_volume, _, _ = _eval_all_axes(
        expanded_mean, volume_fn, "ablation_volume_only", backend, eval_seed
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
    vm_results = []
    for axis, _ in LABEL_AXES:
        train_m, test_m = split_by_config_stratified(
            np.array(config_vm),
            y_vm[axis],
            holdout_fraction=0.25,
            seed=eval_seed + hash(axis) % 997,
        )
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

    mitigation = _mitigation_eval(expanded_mean, backend, eval_seed)

    physical_labels = [lb for _, lb in runs]
    n_arch_physical = count_architectures_in_runs(physical_labels)
    target_archs = all_architecture_ids()

    balance_report: dict = {}
    for axis, fn in LABEL_AXES:
        balance_report[axis] = {
            "physical_counts_before": label_counts_physical(runs, fn),
        }

    def _apply_labeling_gates(results: list[AxisResult]) -> list[dict]:
        out_rows: list[dict] = []
        for r in results:
            d = r.to_dict()
            if r.label_axis in NULL_CLAIM_AXES:
                d["claim_status"] = "NULL"
                d["pass_gate"] = False
                d["notes"] = (
                    (d.get("notes") or "")
                    + " NULL axis: does not beat majority baseline and/or MI "
                    f"< {MI_PASS_FLOOR_BITS} bits — not evaluable for claims"
                ).strip()
            elif r.label_axis == "model_class":
                d["pass_gate"] = False
                d["claim_status"] = "RETRACTED"
                d["notes"] = (
                    (d.get("notes") or "")
                    + " model_class confounded — see docs/architecture_labeling_audit.md"
                ).strip()
            elif r.label_axis == "architecture_id":
                if n_arch_physical < MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM:
                    d["pass_gate"] = False
                    d["claim_status"] = "RETRACTED_INSUFFICIENT_CORPUS"
                else:
                    d["claim_status"] = (
                        "PRELIMINARY_PENDING_HELD_OUT" if r.pass_gate else "NEGATIVE"
                    )
            elif r.label_axis in PRELIMINARY_REAL_AXES:
                d["claim_status"] = (
                    "PRELIMINARY_REAL" if r.pass_gate else "PRELIMINARY"
                )
            else:
                d["claim_status"] = "PRELIMINARY" if r.pass_gate else "NEGATIVE"
            out_rows.append(d)
        return out_rows

    single_gated = _apply_labeling_gates(headline_single)
    mean_gated = _apply_labeling_gates(headline_mean)
    held_arch = held_out_model.get("axes", {}).get("architecture_id", {})
    if held_arch.get("pass_gate") is False or held_arch.get("pass_lower_ci_above_chance") is False:
        for d in single_gated:
            if d["label_axis"] == "architecture_id":
                d["claim_status"] = "NEGATIVE"
                d["pass_gate"] = False
                d["notes"] = (
                    (d.get("notes") or "")
                    + " held-out-model FAIL — no fingerprint claim"
                ).strip()

    architecture_labeling_audit = {
        "doc": "docs/architecture_labeling_audit.md",
        "physical_distinct_architecture_ids": n_arch_physical,
        "target_architecture_ids_in_corpus_spec": target_archs,
        "min_architectures_for_fingerprint": MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
        "explanation": (
            "architecture_id vs model_class disagreement on legacy 2-arch corpus: "
            "model_class is a coarse bucket aligned with train/infer volume; "
            "architecture_id can track config bundles. Only architecture_id is "
            "canonical for fingerprint claims after >=8 physical architectures."
        ),
        "model_class": {"status": "RETRACTED", "report_in_headline": False},
        "architecture_id": {
            "status": (
                "RETRACTED_INSUFFICIENT_CORPUS"
                if n_arch_physical < MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM
                else "CANONICAL_PENDING_GATES"
            ),
            "report_in_headline": n_arch_physical >= MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
        },
    }

    gate_summary = {
        "methodology": "phase1.4 — majority baseline, balanced accuracy + MI pass, balanced config subsample",
        "external_fingerprint_claims": "BLOCKED",
        "architecture_inference_headline": (
            "BLOCKED — held-out-model and balanced multiclass inference fail"
        ),
        "detector_headline": "hard_unauthorized_architecture + adaptive covert (not heavy AUC alone)",
        "null_axes": list(NULL_CLAIM_AXES),
        "preliminary_real_axes": list(PRELIMINARY_REAL_AXES),
        "phase_3": "NOT_APPROVED — gate re-run v1.4 complete; await human review",
    }

    # Interpret ablation: if volume-only ≈ realistic, channel is coarse
    ablation_notes = {}
    for h, v in zip(headline_mean, ablation_volume):
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
        "methodology_version": "phase1.4",
        "metrics_policy": {
            "baseline": "majority_class_on_train",
            "pass_requires": "balanced_accuracy_ci_lower > majority AND mi_bits >= "
            f"{MI_PASS_FLOOR_BITS}",
            "uniform_chance_reported_as": "uniform_chance_accuracy",
            "eval_subsample": "balanced_equal_configs_per_label_value",
        },
        "label_balance_report": balance_report,
        "preliminary_caveats_doc": "docs/PRELIMINARY_CAVEATS.md",
        "external_claims_status": "BLOCKED until scale + held-out-model gates pass",
        "corpus_statistics": stats,
        "corpus_statistics_single_draw": stats_single,
        "observations_per_base_capture": observations_per_base,
        "headline_signal_set": "host_observer_realistic_single_draw",
        "observer_aggregation_labels": {
            "host_observer_realistic_mean_draw": (
                "GENEROUS upper bound: mean of N stochastic observer draws per physical base capture"
            ),
            "host_observer_realistic_single_draw": (
                "REALISTIC: one stochastic observer draw per physical base capture (observation_idx=0)"
            ),
        },
        "architecture_labeling_audit": architecture_labeling_audit,
        "gate_summary": gate_summary,
        "host_observer_realistic_mean_draw": mean_gated,
        "host_observer_realistic_single_draw": single_gated,
        "host_observer_realistic": mean_gated,
        "held_out_model_evaluation": held_out_model,
        "host_observer_idealized": [r.to_dict() for r in idealized],
        "ablation_volume_only": [r.to_dict() for r in ablation_volume],
        "ablation_interpretation": ablation_notes,
        "vm_ground_truth": [r.to_dict() for r in vm_results],
        "learning_curves": learning_curves,
        "mitigation_preview_d3": mitigation,
        "observer_transform_doc": "pipeline/features/realistic_observer.py",
        "split_policy": "config stratified (inference); held_out_model uses architecture_id split",
        "classifier_samples_mean_aggregation": stats.get("physical_base_captures", 0),
        "classifier_samples_single_draw": stats_single.get("physical_base_captures", 0),
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
