"""Generate PHASE_2_REPORT.md from phase2_results.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text("# PHASE 2 Report\n\n**BLOCKED** — run `python3 -m pipeline.cli detect` first.\n")
        return

    d = json.loads(results_path.read_text())
    det = d.get("detector", {})
    caveats = (
        "**PRELIMINARY** — inherits Phase 1 caveats (`docs/PRELIMINARY_CAVEATS.md`). "
        "Not for external writeup or Azure until physical corpus scale gate passes.\n"
    )

    md = f"""# PHASE 2 Report — Policy-Deviation Detector (Gate)

**Date:** 2026-06-03  
**Status:** Gate document (preliminary metrics)  
**Backend:** `{d.get('backend', 'local-gpu')}`  
**Policy:** `{d.get('policy', '')}`

> {caveats}

## 1. Detector definition (D2)

| Item | Value |
|------|--------|
| Signal | `host_observer_realistic_single_draw` (same as Phase 1 realistic headline) |
| Policy | Benign = attested `(mode, architecture_id)` in CVM |
| Violations | Cross-mode / cross-architecture traces (Tier-Red modulator **not** in repo) |
| Model | Logistic regression on policy label |

## 2. Results (test fold)

| Metric | Value |
|--------|--------|
| ROC AUC | **{det.get('roc_auc', 0):.3f}** |
| TPR @ op. point | {det.get('tpr_at_threshold', 0):.3f} |
| FPR @ op. point | {det.get('fpr_at_threshold', 0):.3f} |
| Threshold (95th %ile benign train score) | {det.get('threshold', 0):.4f} |
| TP / FP / TN / FN | {det.get('true_positives')} / {det.get('false_positives')} / {det.get('true_negatives')} / {det.get('false_negatives')} |
| Test samples | {det.get('n_test')} |
| Physical base captures (corpus) | {d.get('physical_base_captures', 'n/a')} |

*Notes:* {det.get('notes', '')}

## 3. Violation types seen in test

```json
{json.dumps(d.get('violation_types_in_test', {}), indent=2)}
```

## 4. Phase 1 gating (unchanged)

| Gate | Status |
|------|--------|
| Single-draw vs mean-draw reporting | See `report/phase1_results.json` → `observer_aggregation_labels` |
| Held-out-model validation | `held_out_model_evaluation` in phase1_results |
| Physical capture scale | Collect with `--repetitions-per-config`; report `physical_base_captures` |

## 5. Azure

**Not run** (Phase 4 only).

---

**STOP — Phase 2 gate.** Await human approval before Phase 3.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase2_results.json", root / "PHASE_2_REPORT.md")
