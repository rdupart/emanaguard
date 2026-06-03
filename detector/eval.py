"""Phase 2 detector — trivial vs hard suites, balanced metrics, covert strength sweep."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc,
    balanced_accuracy_score,
    confusion_matrix,
    roc_curve,
)

from detector.audit import (
    feature_distribution_audit,
    inconsistency_explanation,
    leakage_audit_covert_pairs,
)
from detector.bytes_matched import match_bytes_pairs, timing_structure_features
from detector.covert_modulator import (
    MODULATION_PRESETS,
    apply_covert_modulator,
    search_adaptive_covert_below_threshold,
)
from detector.policy import AttestedPolicy, violation_label
from pipeline.corpus.expand import expand_observations
from pipeline.eval.metrics import majority_baseline
from pipeline.eval.splits import split_by_base_run
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.features.realistic_observer import apply_realistic_observer
from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import (
    ARCHITECTURE_SPECS,
    HARD_CASE_TRAIN_BS,
    HARD_CASE_TRAIN_SL,
    MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
)

HARD_DETECTOR_POLICY = AttestedPolicy(
    name="train_volume_matched_arch_mlp_256x4_only",
    allowed_modes=frozenset({"train"}),
    allowed_architectures=frozenset({"arch_mlp_256x4"}),
)


class ViolationSuite(str, Enum):
    TRIVIAL_MODE = "trivial_mode_change"
    HARD_WRONG_ARCH = "hard_unauthorized_architecture"
    HARD_WRONG_ARCH_BYTES = "hard_unauthorized_architecture_bytes_matched"
    HARD_COVERT_MOD = "hard_covert_modulator"
    HARD_COVERT_LIGHT = "hard_covert_modulator_light"
    HARD_COVERT_ADAPTIVE = "hard_covert_modulator_adaptive"


@dataclass
class DetectorResult:
    suite: str
    policy_name: str
    signal_set: str
    backend: str
    roc_auc: float
    balanced_accuracy: float
    majority_baseline: float
    fpr_at_threshold: float
    tpr_at_threshold: float
    threshold: float
    false_positives: int
    true_positives: int
    false_negatives: int
    true_negatives: int
    n_test: int
    headline: bool
    modulation_strength: str = ""
    notes: str = ""
    margin_bal_over_majority: float = 0.0
    weak_separation: bool = False
    operating_point: dict | None = None
    covert_capacity: dict | None = None
    bytes_matched_meta: dict | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _split_group_id(base_run_id: str) -> str:
    return str(base_run_id).split(":")[0]


def _resolve_attested_architecture(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    policy: AttestedPolicy,
) -> str | None:
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


def _features_from_host(host: list[dict]) -> np.ndarray:
    return host_observer_feature_vector(host)


def _suite_label(
    labels: RunLabels,
    suite: ViolationSuite,
    policy: AttestedPolicy,
    *,
    attested: str | None = None,
) -> int:
    if suite == ViolationSuite.TRIVIAL_MODE:
        return 0 if labels.mode == "train" else 1
    if suite == ViolationSuite.HARD_WRONG_ARCH:
        if labels.mode != "train":
            return 0
        arch = labels.architecture_id or labels.model_class
        return 0 if arch == attested else 1
    return violation_label(labels, policy)


def _build_rows(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    suite: ViolationSuite,
    policy: AttestedPolicy,
    *,
    attested_arch: str | None = None,
    covert_strength: str = "heavy",
    use_adaptive: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    xs, ys, groups = [], [], []
    meta_rows: list[dict] = []
    attested = attested_arch or _resolve_attested_architecture(runs, policy)
    for events, labels in runs:
        if labels.observation_idx != 0:
            continue
        arch = labels.architecture_id or labels.model_class
        gid = _split_group_id(labels.base_run_id)

        if suite in (
            ViolationSuite.HARD_COVERT_MOD,
            ViolationSuite.HARD_COVERT_LIGHT,
            ViolationSuite.HARD_COVERT_ADAPTIVE,
        ):
            if not attested or not _volume_matched_train(labels) or arch != attested:
                continue
            host = project_host_observer(events)
            benign_x = _features(events, labels)
            xs.append(benign_x)
            ys.append(0)
            groups.append(gid)
            strength = (
                "light"
                if suite == ViolationSuite.HARD_COVERT_LIGHT
                else covert_strength
            )
            if suite == ViolationSuite.HARD_COVERT_ADAPTIVE:
                mod = apply_covert_modulator(host, _rng_for(labels), strength="light")
                meta_rows.append({"pending_adaptive_search": True})
            else:
                mod = apply_covert_modulator(
                    host, _rng_for(labels), strength=strength
                )
            xs.append(_features_from_host(mod))
            ys.append(1)
            groups.append(gid)
            continue

        if suite in (ViolationSuite.HARD_WRONG_ARCH, ViolationSuite.HARD_WRONG_ARCH_BYTES):
            if not _volume_matched_train(labels) or not attested:
                continue
            x = _features(events, labels)
            y = 0 if arch == attested else 1
        else:
            x = _features(events, labels)
            y = _suite_label(labels, suite, policy, attested=attested)
        xs.append(x)
        ys.append(y)
        groups.append(gid)

    if not xs:
        return np.empty((0, 0)), np.array([], dtype=int), np.array([], dtype=object), meta_rows
    return np.vstack(xs), np.array(ys), np.array(groups), meta_rows


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
    strength = "light" if suite == ViolationSuite.HARD_COVERT_LIGHT else "heavy"
    x, y, groups, _meta = _build_rows(
        runs,
        suite,
        policy,
        attested_arch=attested,
        covert_strength=strength,
        use_adaptive=False,
    )
    bytes_meta: dict | None = None
    if suite == ViolationSuite.HARD_WRONG_ARCH_BYTES:
        x, y, groups, bytes_meta = match_bytes_pairs(x, y, groups)
        if x.size:
            x = timing_structure_features(x)
    mod_name = ""
    if suite in (
        ViolationSuite.HARD_COVERT_MOD,
        ViolationSuite.HARD_COVERT_LIGHT,
        ViolationSuite.HARD_COVERT_ADAPTIVE,
    ):
        mod_name = (
            "adaptive"
            if suite == ViolationSuite.HARD_COVERT_ADAPTIVE
            else MODULATION_PRESETS.get(strength, MODULATION_PRESETS["heavy"]).name
        )

    if x.size == 0 or len(np.unique(y)) < 2 or len(x) < 8:
        return DetectorResult(
            suite=suite.value,
            policy_name=policy.name,
            signal_set="host_observer_realistic_single_draw",
            backend=backend,
            roc_auc=0.0,
            balanced_accuracy=0.0,
            majority_baseline=0.0,
            fpr_at_threshold=0.0,
            tpr_at_threshold=0.0,
            threshold=0.5,
            false_positives=0,
            true_positives=0,
            false_negatives=0,
            true_negatives=0,
            n_test=0,
            headline=headline,
            modulation_strength=mod_name,
            notes="NEGATIVE: insufficient classes or samples",
        )

    train_m, test_m = split_by_base_run(groups, holdout_fraction=0.2, seed=seed)
    if y[test_m].sum() == 0 or y[test_m].sum() == test_m.sum():
        return DetectorResult(
            suite=suite.value,
            policy_name=policy.name,
            signal_set="host_observer_realistic_single_draw",
            backend=backend,
            roc_auc=0.0,
            balanced_accuracy=0.0,
            majority_baseline=float(majority_baseline(y[train_m])),
            fpr_at_threshold=0.0,
            tpr_at_threshold=0.0,
            threshold=0.5,
            false_positives=0,
            true_positives=0,
            false_negatives=0,
            true_negatives=0,
            n_test=int(test_m.sum()),
            headline=headline,
            modulation_strength=mod_name,
            notes="NEGATIVE: test fold lacks both classes",
        )
    clf = LogisticRegression(max_iter=4000, random_state=seed, class_weight="balanced")
    clf.fit(x[train_m], y[train_m])
    train_benign = clf.predict_proba(x[train_m])[:, 1][y[train_m] == 0]
    thresh = float(np.percentile(train_benign, 95)) if len(train_benign) else 0.5

    covert_cap: dict | None = None
    if suite == ViolationSuite.HARD_COVERT_ADAPTIVE:
        n_evade = 0
        n_try = 0
        for events, labels in runs:
            if labels.observation_idx != 0:
                continue
            arch = labels.architecture_id or labels.model_class
            if not attested or not _volume_matched_train(labels) or arch != attested:
                continue
            if labels.base_run_id not in set(groups[test_m]):
                continue
            host = project_host_observer(events)
            benign_x = _features(events, labels)

            def score_fn(h):
                return float(clf.predict_proba(_features_from_host(h).reshape(1, -1))[0, 1])

            _, ameta = search_adaptive_covert_below_threshold(
                host,
                _rng_for(labels),
                benign_x,
                _features_from_host,
                score_fn,
                threshold=thresh,
            )
            n_try += 1
            if ameta.get("evades_detector"):
                n_evade += 1
        covert_cap = {
            "n_test_attested_traces": n_try,
            "n_evade_at_operating_point": n_evade,
            "fraction_evading": n_evade / max(n_try, 1),
            "operating_threshold": thresh,
        }
        if n_evade == 0:
            covert_cap["covert_capacity_below_op_point"] = (
                "≈zero covert capacity below the detector operating point"
            )

    scores = clf.predict_proba(x[test_m])[:, 1]
    y_test = y[test_m]
    fpr, tpr, _ = roc_curve(y_test, scores)
    roc_auc = float(auc(fpr, tpr)) if len(fpr) > 1 else 0.0
    y_hat_t = (scores >= thresh).astype(int)
    bal_acc = float(balanced_accuracy_score(y_test, y_hat_t))
    maj = float(majority_baseline(y[train_m]))
    margin = bal_acc - maj
    cm = confusion_matrix(y_test, y_hat_t, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    fpr_op = fp / max(fp + tn, 1)
    tpr_op = tp / max(tp + fn, 1)
    op_point = {
        "threshold_95th_percentile_benign_train": thresh,
        "test_fpr": fpr_op,
        "test_tpr": tpr_op,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }
    preset = MODULATION_PRESETS.get(mod_name)
    note = preset.description if preset else ""
    if suite == ViolationSuite.HARD_WRONG_ARCH:
        note = (
            "Reframed: volume-level violation detection at matched (mode, bs=4, seq=128). "
            f"Balanced acc {bal_acc:.3f} vs majority {maj:.3f} (margin {margin:.3f}"
            + (" — WEAK separation" if margin < 0.05 else "") + ")."
        )
    elif suite == ViolationSuite.HARD_WRONG_ARCH_BYTES:
        note = (
            "TRUE total_bytes-matched pairs (±5%), timing/structure features only. "
            f"Pairs={bytes_meta.get('n_pairs', 0) if bytes_meta else 0}. "
            + (
                "Non-volume signal survives."
                if bal_acc > maj + 0.02
                else "No non-volume signal above majority — detection collapses to volume."
            )
        )
    elif suite == ViolationSuite.HARD_COVERT_LIGHT:
        note = MODULATION_PRESETS["light"].description + "; confirm subtle vs heavy"
    elif suite == ViolationSuite.HARD_COVERT_ADAPTIVE:
        note = "Adaptive search for cadence modulation below operating threshold"
    return DetectorResult(
        suite=suite.value,
        policy_name=policy.name,
        signal_set="host_observer_realistic_single_draw",
        backend=backend,
        roc_auc=roc_auc,
        balanced_accuracy=bal_acc,
        majority_baseline=maj,
        fpr_at_threshold=fpr_op,
        tpr_at_threshold=tpr_op,
        threshold=thresh,
        false_positives=int(fp),
        true_positives=int(tp),
        false_negatives=int(fn),
        true_negatives=int(tn),
        n_test=int(test_m.sum()),
        headline=headline,
        modulation_strength=mod_name,
        notes=note,
        margin_bal_over_majority=margin,
        weak_separation=margin < 0.05,
        operating_point=op_point,
        covert_capacity=covert_cap,
        bytes_matched_meta=bytes_meta,
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
    hard_arch_bytes = _eval_suite(
        expanded,
        ViolationSuite.HARD_WRONG_ARCH_BYTES,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 5,
        headline=True,
        attested_arch=attested_arch,
    )
    hard_mod_heavy = _eval_suite(
        expanded,
        ViolationSuite.HARD_COVERT_MOD,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 2,
        headline=False,
        attested_arch=attested_arch,
    )
    hard_mod_light = _eval_suite(
        expanded,
        ViolationSuite.HARD_COVERT_LIGHT,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 3,
        headline=False,
        attested_arch=attested_arch,
    )
    hard_mod_adaptive = _eval_suite(
        expanded,
        ViolationSuite.HARD_COVERT_ADAPTIVE,
        HARD_DETECTOR_POLICY,
        backend,
        eval_seed + 4,
        headline=True,
        attested_arch=attested_arch,
    )

    feat_audit = feature_distribution_audit(runs, attested_arch or "", eval_seed)
    explain = inconsistency_explanation()

    return {
        "methodology_version": "phase2.2",
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
        "modulation_presets": {k: asdict(v) for k, v in MODULATION_PRESETS.items()},
        "headline_detector_metric": (
            "volume-level hard_unauthorized_architecture + bytes_matched timing + adaptive covert capacity"
        ),
        "not_headline": "trivial_mode_change; heavy covert AUC alone; raw AUC without balanced vs majority",
        "external_claim_conditions": (
            "Azure/external: bytes-matched non-volume survival + covert capacity-under-detection required"
        ),
        "detector_inference_audit": {
            "feature_distributions": feat_audit,
            "explanation": explain,
            "leakage": leakage_audit_covert_pairs(),
        },
        "suites": {
            "trivial_mode_change": trivial.to_dict(),
            "hard_unauthorized_architecture_volume_level": hard_arch.to_dict(),
            "hard_unauthorized_architecture_bytes_matched": hard_arch_bytes.to_dict(),
            "hard_covert_modulator_heavy": hard_mod_heavy.to_dict(),
            "hard_covert_modulator_light": hard_mod_light.to_dict(),
            "hard_covert_modulator_adaptive": hard_mod_adaptive.to_dict(),
        },
        "tier_red_note": "covert_modulator.py — measurement transforms only",
    }
