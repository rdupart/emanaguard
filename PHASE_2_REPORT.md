# PHASE 2 Report — Policy-Deviation Detector (Gate)

**Date:** 2026-06-03  
**Status:** Gate document (preliminary metrics)  
**Backend:** `local-gpu`  
**Policy:** `train_only_arch_256x4_1024x8`

> **PRELIMINARY** — inherits Phase 1 caveats (`docs/PRELIMINARY_CAVEATS.md`). Not for external writeup or Azure until physical corpus scale gate passes.


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
| ROC AUC | **1.000** |
| TPR @ op. point | 1.000 |
| FPR @ op. point | 0.046 |
| Threshold (95th %ile benign train score) | 0.0000 |
| TP / FP / TN / FN | 273 / 6 / 124 / 0 |
| Test samples | 403 |
| Physical base captures (corpus) | 2016 |

*Notes:* PRELIMINARY; see docs/PRELIMINARY_CAVEATS.md

## 3. Violation types seen in test

```json
{
  "infer:arch_legacy_small": 140,
  "infer:arch_legacy_large": 133
}
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
