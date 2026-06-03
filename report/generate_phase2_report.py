"""Generate PHASE_2_REPORT.md from phase2_results.json (D2 hard-case suites)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _suite_row(name: str, s: dict) -> str:
    headline = " **HEADLINE**" if s.get("headline") else " (not headline)"
    return (
        f"| {name}{headline} | {s.get('roc_auc', 0):.3f} | {s.get('n_test', 0)} | "
        f"{s.get('tpr_at_threshold', 0):.3f} | {s.get('fpr_at_threshold', 0):.3f} | "
        f"{s.get('notes', '')} |"
    )


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text("# PHASE 2 Report\n\n**BLOCKED** — run `python3 -m pipeline.cli detect` first.\n")
        return

    d = json.loads(results_path.read_text())
    if d.get("backend", "").startswith("simulate"):
        print("Refusing simulate backend.", file=sys.stderr)
        sys.exit(2)

    suites = d.get("suites", {})
    if not suites and "detector" in d:
        # Legacy JSON shape
        suites = {"legacy_combined": d["detector"]}

    caveats = (
        "**PRELIMINARY** — inherits Phase 1 caveats (`docs/PRELIMINARY_CAVEATS.md`). "
        "Headline metrics are **hard** violation suites only. "
        "Trivial mode-change ROC is **not** a result."
    )

    rows = ""
    for key in (
        "hard_unauthorized_architecture",
        "hard_covert_modulator",
        "trivial_mode_change",
    ):
        if key in suites:
            rows += _suite_row(key, suites[key]) + "\n"

    md = f"""# PHASE 2 Report — Policy-Deviation Detector (Gate D2)

**Date:** 2026-06-03  
**Status:** Gate document (preliminary metrics)  
**Backend:** `{d.get('backend', 'local-gpu')}`  
**Headline metric:** `{d.get('headline_detector_metric', 'hard suites')}`  
**Not headline:** `{d.get('not_headline', 'trivial_mode_change')}`

> {caveats}

## 0. Corpus scale (detector inherits Phase 1 gate)

| Item | Value |
|------|--------|
| Physical base captures | {d.get('physical_base_captures', 'n/a')} |
| Distinct `architecture_id` in traces | {d.get('distinct_architecture_ids_in_corpus', 'n/a')} |
| Target architectures (corpus spec) | {len(d.get('target_architectures', []))} listed in JSON |
| Min for fingerprint claim | {d.get('min_architectures_for_fingerprint', 8)} |

## 1. Detector definition (D2)

| Item | Value |
|------|--------|
| Signal | `host_observer_realistic_single_draw` |
| Attested policy | `{suites.get('hard_unauthorized_architecture', {}).get('policy_name', 'train_volume_matched_arch_mlp_256x4_only')}` |
| Hard (a) | Unauthorized architecture at **same** train mode/volume profile |
| Hard (b) | Covert modulator on attested benign trace (Tier-Red transform in repo for measurement) |
| Not a result | Mode change alone (`trivial_mode_change`) |

*{d.get('tier_red_note', '')}*

## 2. ROC by suite (test fold)

| Suite | ROC AUC | n_test | TPR | FPR | Notes |
|-------|---------|--------|-----|-----|-------|
{rows or '| (no suites in JSON) | — | — | — | — | re-run detect |'}

## 3. Phase 1 gating (unchanged)

| Gate | Status |
|------|--------|
| Labeling audit (`architecture_id` vs `model_class`) | `docs/architecture_labeling_audit.md` + `architecture_labeling_audit` in phase1 JSON |
| ≥8 physical architectures | Re-collect on expanded corpus |
| Held-out-model (single-draw) | `held_out_model_evaluation` in phase1_results |
| Single-draw headline | `host_observer_realistic_single_draw` |

## 4. Azure

**Not run** (Phase 4 only).

---

**STOP — Phase 2 gate.** Phase 3 **not approved** until hard-case detector + Phase 1 gates pass on scaled corpus.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase2_results.json", root / "PHASE_2_REPORT.md")
