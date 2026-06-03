"""Generate PHASE_2_REPORT.md from phase2_results.json (D2 v2.2)."""

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
    return (
        f"| {name}{headline}{mod_s} | {s.get('roc_auc', 0):.3f} | "
        f"{s.get('balanced_accuracy', 0):.3f} | {s.get('majority_baseline', 0):.3f} | "
        f"{margin:.3f}{weak} | {s.get('n_test', 0)} | "
        f"{(s.get('operating_point') or {}).get('test_fpr', 0):.3f} | "
        f"{(s.get('notes') or '')[:60]} |"
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

    covert = suites.get("hard_covert_modulator_adaptive", {}).get("covert_capacity", {})

    md = f"""# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.2)

**Methodology:** `{d.get('methodology_version', 'phase2.2')}`  
**Backend:** `{d.get('backend')}`  

> **PRELIMINARY (local).** External/Azure gated — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.
> Prominent metric: **balanced accuracy vs majority baseline** (not raw AUC alone).

## 1. Suites

| Suite | ROC AUC | Bal.Acc | Maj.base | Margin | n_test | FPR@op | Notes |
|-------|---------|---------|----------|--------|--------|--------|-------|
{rows or '| — | — | — | — | — | — | — | — |'}

## 2. Detector honesty

**Volume-level** (`hard_unauthorized_architecture_volume_level`): detects wrong architecture at matched (mode, bs=4, seq=128). Margin over majority is often **small (<0.05 = WEAK)** even when AUC is high.

**Bytes-matched** (`hard_unauthorized_architecture_bytes_matched`): ±10% total_bytes pairing, timing/structure features only.

**Compute confound:** `{feat.get('compute_volume_confound_at_matched_bs_seq', 'see JSON')}` — `{feat.get('headline_retraction_risk', '')}`

## 3. Covert capacity under detector

Adaptive result: `{covert.get('covert_capacity_below_op_point', covert)}`  
Test FPR @ operating point: `{suites.get('hard_covert_modulator_adaptive', {}).get('operating_point', {})}`

Heavy/light AUC≈1 is **not** a strong security claim.

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.2.**
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase2_results.json", root / "PHASE_2_REPORT.md")
