# PHASE 2 Report — Policy-Deviation Detector (Gate D2)

**Date:** 2026-06-03  
**Status:** Gate document (preliminary metrics)  
**Backend:** `local-gpu`  
**Headline metric:** `hard_unauthorized_architecture + hard_covert_modulator`  
**Not headline:** `trivial_mode_change (volume/mode only)`

> **PRELIMINARY** — inherits Phase 1 caveats (`docs/PRELIMINARY_CAVEATS.md`). Headline metrics are **hard** violation suites only. Trivial mode-change ROC is **not** a result.

## 0. Corpus scale (detector inherits Phase 1 gate)

| Item | Value |
|------|--------|
| Physical base captures | 4576 |
| Distinct `architecture_id` in traces | 12 |
| Target architectures (corpus spec) | 10 listed in JSON |
| Min for fingerprint claim | 8 |

## 1. Detector definition (D2)

| Item | Value |
|------|--------|
| Signal | `host_observer_realistic_single_draw` |
| Attested policy | `train_volume_matched_arch_mlp_256x4_only` |
| Hard (a) | Unauthorized architecture at **same** train mode/volume profile |
| Hard (b) | Covert modulator on attested benign trace (Tier-Red transform in repo for measurement) |
| Not a result | Mode change alone (`trivial_mode_change`) |

*covert_modulator.py implements measurement transform; not published as exploit*

## 2. ROC by suite (test fold)

| Suite | ROC AUC | n_test | TPR | FPR | Notes |
|-------|---------|--------|-----|-----|-------|
| hard_unauthorized_architecture **HEADLINE** | 0.995 | 321 | 0.932 | 0.000 | PRELIMINARY — not for external claims until >=8 physical architectures collected |
| hard_covert_modulator **HEADLINE** | 1.000 | 64 | 1.000 | 0.034 | PRELIMINARY — not for external claims until >=8 physical architectures collected |
| trivial_mode_change (not headline) | 1.000 | 915 | 1.000 | 0.028 | PRELIMINARY — not for external claims until >=8 physical architectures collected |


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
