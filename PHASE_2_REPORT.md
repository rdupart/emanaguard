# PHASE 2 Report — Policy-Deviation Detector (Gate D2 v2.3)

**Methodology:** `phase2.3`  
**Backend:** `local-gpu`  

> **PRELIMINARY (local).** External/Azure gated — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.
> Prominent metric: **balanced accuracy vs majority baseline** (not raw AUC alone).

## 1. Suites

| Suite | ROC AUC | Bal.Acc | Maj.base | Margin | n_test | FPR@op | Notes |
|-------|---------|---------|----------|--------|--------|--------|-------|
| hard_unauthorized_architecture_volume_level **HEADLINE** | 0.989 | 0.979 | 0.898 | 0.081 | 321 | 0.000 | Reframed: volume-level violation detection at matched (mode, bs=4, seq=1 |
| hard_unauthorized_architecture_bytes_matched **HEADLINE** [UNTESTABLE_OPEN_QUESTION] | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0.000 | No benign/violation pairs within ±10% total_bytes on this corpus; non-vo |
| hard_covert_modulator_adaptive **HEADLINE** (adaptive) | 1.000 | 0.984 | 0.500 | 0.484 | 64 | 0.031 | Continuous cadence-amplitude sweep to feature noise floor. Tested contin |
| hard_covert_modulator_light (light) | 1.000 | 0.969 | 0.500 | 0.469 | 64 | 0.062 | Low cadence shift (~8% jitter) — subtle timing perturbation; confirm sub |
| hard_covert_modulator_heavy (heavy) | 1.000 | 0.953 | 0.500 | 0.453 | 64 | 0.094 | Strong cadence quantization — legacy default |
| trivial_mode_change | 1.000 | 0.977 | 0.505 | 0.472 | 915 | 0.046 |  |


## 2. Detector honesty

**Volume-level** (`hard_unauthorized_architecture_volume_level`): detects wrong architecture at matched (mode, bs=4, seq=128). Margin over majority is often **small (<0.05 = WEAK)** even when AUC is high.

**Bytes-matched** (`hard_unauthorized_architecture_bytes_matched`): status **`UNTESTABLE_OPEN_QUESTION`**.  
0 pairs at ±10% tolerance.  
No benign/violation pairs within ±10% total_bytes on this corpus; non-volume detector survival cannot be measured — not a resolved negative.

**Compute confound:** `True` — `PARTIAL — hard_unauthorized_architecture tracks architecture-correlated transfer volume at matched knobs, not covert policy alone`

## 3. Covert capacity under detector

**Claim (v2.3):** Tested continuous cadence sweep (0.02–4.0× light baseline): no scale evades detector at operating point on held-out attested traces; adaptive-adversary covert capacity NOT established (preset-only evasion search retired).

Amplitude sweep traces: `32` held-out attested; any evasion in sweep: `False`.

Heavy/light preset AUC≈1 is **not** a strong security claim — presets are detectable; continuous sweep establishes detectability vs cadence scale.

## 4. Azure

Not run.

---

**STOP — Phase 2 gate v2.3.**
