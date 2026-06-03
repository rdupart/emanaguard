"""Phase 1 end-to-end evaluation — separate signal sets (a) and (b)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pipeline.eval.classifiers import fit_predict, make_logreg, make_rf, make_sequence_clf
from pipeline.eval.metrics import AxisResult, evaluate_predictions
from pipeline.eval.splits import mask_for_seeds, split_by_seed
from pipeline.features.host_observer import (
    host_observer_feature_vector,
    host_observer_sequence,
    project_host_observer,
)
from pipeline.features.vm_ground_truth import vm_ground_truth_feature_vector
from pipeline.trace.events import RunLabels, TransferEvent

LABEL_AXES = [
    ("mode", lambda lb: lb.mode),
    ("model_class", lambda lb: lb.model_class),
    ("batch_size", lambda lb: str(lb.batch_size)),
    ("seq_length", lambda lb: str(lb.seq_length)),
    ("llm_phase", lambda lb: lb.llm_phase),
]


@dataclass
class EvalBundle:
    backend: str
    vm_results: list[AxisResult]
    host_results: list[AxisResult]
    host_sequence_results: list[AxisResult]

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "vm_ground_truth": [r.to_dict() for r in self.vm_results],
            "host_observer": [r.to_dict() for r in self.host_results],
            "host_observer_sequence": [r.to_dict() for r in self.host_sequence_results],
        }


def _stack_features(
    runs: list[tuple[list[TransferEvent], RunLabels]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    vm_rows: list[np.ndarray] = []
    host_rows: list[np.ndarray] = []
    seq_rows: list[np.ndarray] = []
    ys: dict[str, list[str]] = {ax: [] for ax, _ in LABEL_AXES}
    seeds: list[int] = []

    for events, labels in runs:
        host_ev = project_host_observer(events)
        vm_rows.append(vm_ground_truth_feature_vector(events))
        host_rows.append(host_observer_feature_vector(host_ev))
        seq_rows.append(host_observer_sequence(host_ev))
        seeds.append(labels.seed)
        for ax, fn in LABEL_AXES:
            ys[ax].append(fn(labels))

    return (
        np.vstack(vm_rows),
        np.vstack(host_rows),
        np.vstack(seq_rows),
        np.array(seeds),
    ), {k: np.array(v) for k, v in ys.items()}


def _eval_axis(
    x: np.ndarray,
    y: np.ndarray,
    seeds: np.ndarray,
    label_axis: str,
    signal_set: str,
    backend: str,
    train_seeds: list[int],
    test_seeds: list[int],
    clf_factory,
    seed: int,
) -> AxisResult:
    train_m = mask_for_seeds(seeds, train_seeds)
    test_m = mask_for_seeds(seeds, test_seeds)
    classes = np.unique(y)

    if len(classes) < 2:
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y)),
            n_classes=len(classes),
            chance_accuracy=1.0,
            accuracy=float((y == y[0]).mean()) if len(y) else 0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            confusion=[[int(len(y))]] if len(y) else [[]],
            class_names=[str(c) for c in classes],
            notes="NEGATIVE: single class in corpus — axis not separable",
        )

    if train_m.sum() < 2 or test_m.sum() < 1:
        return AxisResult(
            label_axis=label_axis,
            signal_set=signal_set,
            backend=backend,
            n_samples=int(len(y)),
            n_classes=len(classes),
            chance_accuracy=0.0,
            accuracy=0.0,
            mi_bits=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            pass_lower_ci_above_chance=False,
            confusion=[],
            class_names=[str(c) for c in classes],
            notes="insufficient train/test split",
        )

    clf = clf_factory(seed)
    y_pred_test = fit_predict(clf, x[train_m], y[train_m], x[test_m])

    return evaluate_predictions(
        y[test_m],
        y_pred_test,
        class_names=[str(c) for c in classes],
        label_axis=label_axis,
        signal_set=signal_set,
        backend=backend,
    )


def run_evaluation(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    backend: str,
    seeds: list[int],
    eval_seed: int = 42,
) -> EvalBundle:
    train_seeds, test_seeds = split_by_seed(
        seeds, holdout_fraction=0.25, seed_for_split=eval_seed
    )

    (x_vm, x_host, x_seq, seeds_arr), y_dict = _stack_features(runs)

    vm_results: list[AxisResult] = []
    host_results: list[AxisResult] = []
    seq_results: list[AxisResult] = []

    for axis, _ in LABEL_AXES:
        y = y_dict[axis]
        vm_results.append(
            _eval_axis(
                x_vm,
                y,
                seeds_arr,
                axis,
                "vm_ground_truth",
                backend,
                train_seeds,
                test_seeds,
                make_rf,
                eval_seed,
            )
        )
        host_results.append(
            _eval_axis(
                x_host,
                y,
                seeds_arr,
                axis,
                "host_observer",
                backend,
                train_seeds,
                test_seeds,
                make_logreg,
                eval_seed,
            )
        )
        seq_results.append(
            _eval_axis(
                x_seq,
                y,
                seeds_arr,
                axis,
                "host_observer_sequence",
                backend,
                train_seeds,
                test_seeds,
                make_sequence_clf,
                eval_seed,
            )
        )

    return EvalBundle(
        backend=backend,
        vm_results=vm_results,
        host_results=host_results,
        host_sequence_results=seq_results,
    )
