"""Generate PHASE_2_REPORT.md from phase2_results.json (D2 v2.1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _suite_row(name: str, s: dict) -> str:
    headline = " **HEADLINE**" if s.get("headline") else ""
    mod = s.get("modulation_strength", "")
    mod_s = f" ({mod})" if mod else ""
    return (
        f"| {name}{headline}{mod_s} | {s.get('roc_auc', 0):.3f} | "
        f"{s.get('balanced_accuracy', 0):.3f} | {s.get('majority_baseline', 0):.3f} | "
        f"{s.get('n_test', 0)} | {s.get('notes', '')[:80]} |"
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

    rows = ""
    for key in (
        "hard_unauthorized_architecture",
        "hard_covert_modulator_adaptive",
        "hard_covert_modulator_light",
        "hard_covert_modulator_heavy",
        "trivial_mode_change",
    ):
        if key in suites:
            rows += _suite_row(key, suites[key]) + "\n"

    feat = audit.get("feature_distributions", {})
    interp = feat.get("interpretation", audit.get("explanation", {}).get("why_binary_can_exceed_multiclass", ""))

    md = f"""# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.1)

**Date:** 2026-06-03  
**Methodology:** `{d.get('methodology_version', 'phase2.1')}`  
**Backend:** `{d.get('backend', 'local-gpu')}`  

> **PRELIMINARY** — Phase 3 not approved. Headline: **balanced** detector metrics + **adaptive** covert modulator.
> Heavy covert AUC≈1 alone is **not** a strong claim. See `docs/detector_inference_inconsistency.md`.

## 1. ROC / balanced accuracy by suite

| Suite | ROC AUC | Bal.Acc | Maj.base | n_test | Notes |
|-------|---------|---------|----------|--------|-------|
{rows or '| — | — | — | — | — | — |'}

**Headline:** `{d.get('headline_detector_metric', '')}`  
**Not headline:** `{d.get('not_headline', '')}`

## 2. Detector vs 12-way inference

{interp}

Feature audit (`volume_matched_on_coarse_features`): **{feat.get('volume_matched_on_coarse_features', 'n/a')}**  
Mean L2 (benign vs wrong-arch): **{feat.get('mean_feature_l2_benign_vs_wrong_arch', 'n/a')}**

## 3. Modulation presets

```json
{json.dumps(d.get('modulation_presets', {}), indent=2)[:2000]}
```

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.1.** Phase 3 blocked.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report/phase2_results.json", root / "PHASE_2_REPORT.md")
