"""Generate PHASE_2_REPORT.md from phase2_results.json (D2 v2.3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _suite_row(name: str, s: dict) -> str:
    headline = " **HEADLINE**" if s.get("headline") else ""
    mod = s.get("modulation_strength", "")
    mod_s = f" ({mod})" if mod else ""
    margin = s.get("margin_bal_over_majority", 0)
    weak = " **WEAK**" if s.get("weak_separation") else ""
    status = s.get("suite_status", "EVALUATED")
    status_s = f" [{status}]" if status != "EVALUATED" else ""
    return (
        f"| {name}{headline}{mod_s}{status_s} | {s.get('roc_auc', 0):.3f} | "
        f"{s.get('balanced_accuracy', 0):.3f} | {s.get('majority_baseline', 0):.3f} | "
        f"{margin:.3f}{weak} | {s.get('n_test', 0)} | "
        f"{(s.get('operating_point') or {}).get('test_fpr', 0):.3f} | "
        f"{(s.get('notes') or '')[:72]} |"
    )


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text("# PHASE 2 Report\n\n**BLOCKED** — run detect first.\n")
        return

    d = json.loads(results_path.read_text())
    if d.get("backend", "").startswith("simulate"):
        print("Refusing simulate backend.", file=sys.stderr)
        sys.exit(2)

    suites = d.get("suites", {})
    audit = d.get("detector_inference_audit", {})
    feat = audit.get("feature_distributions", {})

    rows = ""
    for key in (
        "hard_unauthorized_architecture_volume_level",
        "hard_unauthorized_architecture_bytes_matched",
        "hard_covert_modulator_adaptive",
        "hard_covert_modulator_light",
        "hard_covert_modulator_heavy",
        "trivial_mode_change",
    ):
        if key in suites:
            rows += _suite_row(key, suites[key]) + "\n"

    bm = suites.get("hard_unauthorized_architecture_bytes_matched", {})
    bm_meta = bm.get("bytes_matched_meta") or {}
    n_pairs = bm_meta.get("n_pairs", 0)
    bm_status = bm.get("suite_status", bm_meta.get("suite_status", "EVALUATED"))
    covert = suites.get("hard_covert_modulator_adaptive", {}).get("covert_capacity", {})
    cap_claim = covert.get(
        "covert_capacity_claim",
        covert.get("covert_capacity_below_op_point", "see JSON curve"),
    )

    md = f"""# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.3)

**Methodology:** `{d.get('methodology_version', 'phase2.3')}`  
**Backend:** `{d.get('backend')}`  

> **PRELIMINARY (local).** External/Azure gated — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.
> Prominent metric: **balanced accuracy vs majority baseline** (not raw AUC alone).

## 1. Suites

| Suite | ROC AUC | Bal.Acc | Maj.base | Margin | n_test | FPR@op | Notes |
|-------|---------|---------|----------|--------|--------|--------|-------|
{rows or '| — | — | — | — | — | — | — | — |'}

## 2. Detector honesty

**Volume-level** (`hard_unauthorized_architecture_volume_level`): detects wrong architecture at matched (mode, bs=4, seq=128). Margin over majority is often **small (<0.05 = WEAK)** even when AUC is high.

**Bytes-matched** (`hard_unauthorized_architecture_bytes_matched`): status **`{bm_status}`**.  
{n_pairs} pairs at ±10% tolerance.  
{bm_meta.get('interpretation', bm.get('notes', 'See phase2_results.json'))}

**Compute confound:** `{feat.get('compute_volume_confound_at_matched_bs_seq', 'see JSON')}` — `{feat.get('headline_retraction_risk', '')}`

## 3. Covert capacity under detector

**Claim (v2.3):** {cap_claim}

Amplitude sweep traces: `{covert.get('n_traces', 0)}` held-out attested; any evasion in sweep: `{covert.get('any_evasion_in_sweep', 'n/a')}`.

Heavy/light preset AUC≈1 is **not** a strong security claim — presets are detectable; continuous sweep establishes detectability vs cadence scale.

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.3.**
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase2_results.json", root / "PHASE_2_REPORT.md")
