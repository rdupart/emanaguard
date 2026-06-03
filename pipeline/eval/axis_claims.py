"""Axis claim status and NULL rationale (verdict must match reported numbers)."""

from __future__ import annotations

from pipeline.eval.metrics import MI_PASS_FLOOR_BITS, AxisResult

VOLUME_CONFOUND_NOTE = "volume-confounded (total-bytes ablation ≈ full observer)"
MINORITY_FRAGILITY_MIN_SUPPORT = 16


def null_rationale(
    axis: str,
    result: AxisResult,
    ablation_interpretation: dict[str, str],
    *,
    balanced_eval_min_class_support: int | None = None,
) -> str:
    """Explain why an axis is NULL despite metrics that may beat majority."""
    parts: list[str] = []
    if axis in ablation_interpretation:
        parts.append(ablation_interpretation[axis])
    elif result.label_axis in ablation_interpretation:
        parts.append(ablation_interpretation[result.label_axis])

    min_support = MINORITY_FRAGILITY_MIN_SUPPORT
    if balanced_eval_min_class_support is not None:
        min_support = min(min_support, balanced_eval_min_class_support)
    minority = [
        c
        for c, n in result.per_class_support.items()
        if n > 0 and n < min_support
    ]
    if minority:
        parts.append(
            f"minority-class fragility (per-class support {result.per_class_support}; "
            f"classes with n<{min_support}: {minority})"
        )

    if result.pass_balanced_beat_majority and result.pass_mi_above_floor:
        parts.append(
            "metrics beat majority and pass MI floor but axis is not claimable "
            "(confound / fragility — not a fine-grained channel)"
        )
    elif not result.pass_balanced_beat_majority:
        parts.append(
            f"balanced accuracy {result.balanced_accuracy:.3f} does not beat "
            f"majority baseline {result.majority_baseline_accuracy:.3f}"
        )
    if not result.pass_mi_above_floor:
        parts.append(f"MI {result.mi_bits:.3f} < {MI_PASS_FLOOR_BITS} bits")

    return "; ".join(parts) if parts else "not evaluable for external claims"


def assign_claim_status(
    result: AxisResult,
    *,
    axis: str,
    null_axes_volume: frozenset[str],
    ablation_interpretation: dict[str, str],
    n_arch_physical: int,
    min_arch_for_fingerprint: int,
    held_out_arch_pass: bool | None = None,
) -> tuple[str, bool, str]:
    """
    Returns (claim_status, pass_gate_for_report, notes_suffix).
    """
    notes = result.notes or ""

    if axis == "model_class":
        return "RETRACTED", False, notes + " model_class confounded"

    if axis in null_axes_volume:
        rationale = null_rationale(axis, result, ablation_interpretation)
        return "NULL", False, rationale

    if axis == "architecture_id":
        if n_arch_physical < min_arch_for_fingerprint:
            return "RETRACTED_INSUFFICIENT_CORPUS", False, notes
        if held_out_arch_pass is False:
            return "NEGATIVE", False, notes + " held-out-model FAIL"
        return ("PRELIMINARY_PENDING_HELD_OUT" if result.pass_gate else "NEGATIVE"), result.pass_gate, notes

    if axis in ("mode", "batch_size"):
        status = "PRELIMINARY_REAL" if result.pass_gate else "PRELIMINARY"
        return status, result.pass_gate, notes

    return ("PRELIMINARY" if result.pass_gate else "NEGATIVE"), result.pass_gate, notes


def audit_verdicts_vs_numbers(rows: list[dict]) -> list[dict]:
    """Flag rows where claim_status contradicts reported metrics."""
    issues: list[dict] = []
    for d in rows:
        axis = d["label_axis"]
        status = d.get("claim_status", "")
        bal = d.get("balanced_accuracy", 0)
        maj = d.get("majority_baseline_accuracy", d.get("chance_accuracy", 0))
        mi = d.get("mi_bits", 0)
        pass_gate = d.get("pass_gate", d.get("pass_lower_ci_above_chance"))

        if status == "NULL" and pass_gate and axis not in ("llm_phase", "seq_length"):
            issues.append(
                {
                    "axis": axis,
                    "issue": "NULL status but pass_gate=True",
                    "bal": bal,
                    "maj": maj,
                    "mi": mi,
                }
            )
        if status == "PRELIMINARY_REAL" and not pass_gate:
            issues.append(
                {"axis": axis, "issue": "PRELIMINARY_REAL but pass_gate=False", "bal": bal, "maj": maj}
            )
        if status == "NULL" and axis == "llm_phase" and bal >= maj and mi >= MI_PASS_FLOOR_BITS:
            if VOLUME_CONFOUND_NOTE.split("(")[0].strip() not in (d.get("notes") or ""):
                issues.append(
                    {
                        "axis": "llm_phase",
                        "issue": "llm_phase NULL should cite volume-confound (metrics beat majority)",
                        "bal": bal,
                        "maj": maj,
                        "mi": mi,
                    }
                )
    return issues
