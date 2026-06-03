# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.2)

**Methodology:** `phase2.2`  
**Backend:** `local-gpu`  

> **PRELIMINARY (local).** External/Azure gated — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.
> Prominent metric: **balanced accuracy vs majority baseline** (not raw AUC alone).

## 1. Suites

| Suite | ROC AUC | Bal.Acc | Maj.base | Margin | n_test | FPR@op | Notes |
|-------|---------|---------|----------|--------|--------|--------|-------|
| hard_unauthorized_architecture_volume_level **HEADLINE** | 0.983 | 0.933 | 0.898 | 0.035 **WEAK** | 321 | 0.103 | Reframed: volume-level violation detection at matched (mode, |
| hard_unauthorized_architecture_bytes_matched **HEADLINE** | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0.000 | NEGATIVE: insufficient classes or samples |
| hard_covert_modulator_adaptive **HEADLINE** (adaptive) | 1.000 | 1.000 | 0.500 | 0.500 | 64 | 0.000 | Adaptive search for cadence modulation below operating thres |
| hard_covert_modulator_light (light) | 1.000 | 0.953 | 0.500 | 0.453 | 64 | 0.094 | Low cadence shift (~8% jitter) — subtle timing perturbation; |
| hard_covert_modulator_heavy (heavy) | 1.000 | 0.969 | 0.500 | 0.469 | 64 | 0.062 | Strong cadence quantization — legacy default |
| trivial_mode_change | 1.000 | 0.978 | 0.505 | 0.473 | 915 | 0.044 |  |


## 2. Detector honesty

**Volume-level** (`hard_unauthorized_architecture_volume_level`): detects wrong architecture at matched (mode, bs=4, seq=128). Margin over majority is often **small (<0.05 = WEAK)** even when AUC is high.

**Bytes-matched** (`hard_unauthorized_architecture_bytes_matched`): ±10% total_bytes pairing, timing/structure features only.

**Compute confound:** `True` — `PARTIAL — hard_unauthorized_architecture tracks architecture-correlated transfer volume at matched knobs, not covert policy alone`

## 3. Covert capacity under detector

Adaptive result: `≈zero covert capacity below the detector operating point`  
Test FPR @ operating point: `{'threshold_95th_percentile_benign_train': 2.741226552404674e-12, 'test_fpr': 0.0, 'test_tpr': 1.0, 'tp': 32, 'fp': 0, 'tn': 32, 'fn': 0}`

Heavy/light AUC≈1 is **not** a strong security claim.

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.2.**
