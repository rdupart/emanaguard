from __future__ import annotations

from pipeline.eval.axis_claims import assign_claim_status, null_rationale
from pipeline.eval.metrics import AxisResult


def test_llm_phase_null_rationale_mentions_volume_not_majority_fail():
    r = AxisResult(
        label_axis="llm_phase",
        signal_set="t",
        backend="t",
        n_samples=10,
        n_classes=3,
        chance_accuracy=0.33,
        majority_baseline_accuracy=0.33,
        uniform_chance_accuracy=0.33,
        accuracy=1.0,
        balanced_accuracy=1.0,
        macro_f1=1.0,
        mi_bits=0.368,
        ci_lower=0.9,
        ci_upper=1.0,
        balanced_ci_lower=0.9,
        balanced_ci_upper=1.0,
        pass_lower_ci_above_chance=False,
        pass_balanced_beat_majority=True,
        pass_mi_above_floor=True,
        pass_gate=False,
        confusion=[],
        class_names=["n/a", "prefill", "decode"],
        per_class_recall={"prefill": 1.0, "decode": 1.0, "n/a": 1.0},
        per_class_support={"prefill": 8, "decode": 8, "n/a": 100},
    )
    ablation = {
        "llm_phase": "Coarse volume leakage: total-bytes ablation within 5% of full realistic features."
    }
    status, pass_g, notes = assign_claim_status(
        r,
        axis="llm_phase",
        null_axes_volume=frozenset({"llm_phase"}),
        ablation_interpretation=ablation,
        n_arch_physical=12,
        min_arch_for_fingerprint=8,
    )
    assert status == "NULL"
    assert pass_g is False
    assert "volume" in notes.lower()
    assert "minority" in notes.lower() or "fragility" in notes.lower()
