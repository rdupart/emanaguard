#!/usr/bin/env python3
"""Re-apply v1.4 axis claim labels to existing phase1_results.json (no full re-eval)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.eval.axis_claims import assign_claim_status, audit_verdicts_vs_numbers
from pipeline.eval.metrics import AxisResult, MI_PASS_FLOOR_BITS
from pipeline.workloads.corpus import MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM

VOLUME_NULL = frozenset({"llm_phase"})


def main() -> int:
    path = ROOT / "report" / "phase1_results.json"
    data = json.loads(path.read_text())
    ablation = data.get("ablation_interpretation", {})
    held = data.get("held_out_model_evaluation", {}).get("axes", {}).get("architecture_id", {})
    held_pass = held.get("pass_gate", held.get("pass_lower_ci_above_chance", False))
    n_arch = data.get("architecture_labeling_audit", {}).get(
        "physical_distinct_architecture_ids", 12
    )

    def refresh(rows: list[dict]) -> list[dict]:
        out = []
        for d in rows:
            r = AxisResult(
                label_axis=d["label_axis"],
                signal_set=d.get("signal_set", ""),
                backend=d.get("backend", "local-gpu"),
                n_samples=d.get("n_samples", 0),
                n_classes=d.get("n_classes", 0),
                chance_accuracy=d.get("majority_baseline_accuracy", d.get("chance_accuracy", 0)),
                majority_baseline_accuracy=d.get(
                    "majority_baseline_accuracy", d.get("chance_accuracy", 0)
                ),
                uniform_chance_accuracy=d.get("uniform_chance_accuracy", 0.25),
                accuracy=d.get("accuracy", 0),
                balanced_accuracy=d.get("balanced_accuracy", 0),
                macro_f1=d.get("macro_f1", 0),
                mi_bits=d.get("mi_bits", 0),
                ci_lower=d.get("ci_lower", 0),
                ci_upper=d.get("ci_upper", 0),
                balanced_ci_lower=d.get("balanced_ci_lower", 0),
                balanced_ci_upper=d.get("balanced_ci_upper", 0),
                pass_lower_ci_above_chance=d.get("pass_gate", False),
                pass_balanced_beat_majority=d.get("pass_balanced_beat_majority", False),
                pass_mi_above_floor=d.get("pass_mi_above_floor", False),
                pass_gate=d.get("pass_gate", False),
                confusion=d.get("confusion", []),
                class_names=d.get("class_names", []),
                per_class_recall=d.get("per_class_recall", {}),
                per_class_support=d.get("per_class_support", {}),
            )
            status, pass_g, notes = assign_claim_status(
                r,
                axis=r.label_axis,
                null_axes_volume=VOLUME_NULL,
                ablation_interpretation=ablation,
                n_arch_physical=n_arch,
                min_arch_for_fingerprint=MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM,
                held_out_arch_pass=held_pass if r.label_axis == "architecture_id" else None,
            )
            if r.label_axis == "seq_length" and (
                not r.pass_gate or r.label_axis in ablation
            ):
                from pipeline.eval.axis_claims import null_rationale

                status, pass_g, notes = "NULL", False, null_rationale(
                    r.label_axis, r, ablation
                )
            nd = dict(d)
            nd["claim_status"] = status
            nd["pass_gate"] = pass_g
            nd["notes"] = notes
            out.append(nd)
        return out

    for key in ("host_observer_realistic_single_draw", "host_observer_realistic_mean_draw"):
        if key in data:
            data[key] = refresh(data[key])
    data["axis_verdict_audit"] = audit_verdicts_vs_numbers(
        data.get("host_observer_realistic_single_draw", [])
    )
    gs = data.setdefault("gate_summary", {})
    gs["llm_phase_null_rationale"] = (
        "volume-confounded (total-bytes ablation ≈ 1.0) + minority-class fragility; "
        "NOT because metrics fail majority"
    )
    gs["phase_3"] = "APPROVED (local mitigation) — external/Azure gated"
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Refreshed {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
