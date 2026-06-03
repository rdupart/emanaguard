# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.1)

**Date:** 2026-06-03  
**Methodology:** `phase2.1`  
**Backend:** `local-gpu`  

> **PRELIMINARY** — Phase 3 not approved. Headline: **balanced** detector metrics + **adaptive** covert modulator.
> Heavy covert AUC≈1 alone is **not** a strong claim. See `docs/detector_inference_inconsistency.md`.

## 1. ROC / balanced accuracy by suite

| Suite | ROC AUC | Bal.Acc | Maj.base | n_test | Notes |
|-------|---------|---------|----------|--------|-------|
| hard_unauthorized_architecture **HEADLINE** | 0.987 | 0.935 | 0.898 | 321 |  |
| hard_covert_modulator_adaptive **HEADLINE** (adaptive) | 1.000 | 1.000 | 0.500 | 64 | Adaptive adversary: weakest preset that changes features; reports covert capacit |
| hard_covert_modulator_light (light) | 1.000 | 1.000 | 0.500 | 64 | Low cadence shift (~8% jitter) — subtle timing perturbation |
| hard_covert_modulator_heavy (heavy) | 1.000 | 1.000 | 0.500 | 64 | Strong cadence quantization (legacy default) — easy to detect |
| trivial_mode_change | 1.000 | 1.000 | 0.505 | 915 |  |


**Headline:** `hard_unauthorized_architecture (balanced acc) + hard_covert_modulator_adaptive`  
**Not headline:** `trivial_mode_change; heavy covert AUC alone`

## 2. Detector vs 12-way inference

At fixed (mode, bs, seq), wrong-architecture rows still differ in total_bytes because model hidden/layers change transfer volume. Binary detector can separate attested vs other arch using this compute-volume proxy; 12-way inference fails under realistic noise. NOT a pure policy violation at identical byte volume.

Feature audit (`volume_matched_on_coarse_features`): **False**  
Mean L2 (benign vs wrong-arch): **n/a**

## 3. Modulation presets

```json
{
  "light": {
    "name": "light",
    "cadence_ns": 80000,
    "jitter_fraction": 0.08,
    "description": "Low cadence shift (~8% jitter) \u2014 subtle timing perturbation"
  },
  "medium": {
    "name": "medium",
    "cadence_ns": 200000,
    "jitter_fraction": 0.15,
    "description": "Moderate cadence replacement"
  },
  "heavy": {
    "name": "heavy",
    "cadence_ns": 350000,
    "jitter_fraction": 0.25,
    "description": "Strong cadence quantization (legacy default) \u2014 easy to detect"
  }
}
```

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.1.** Phase 3 blocked.
