# PHASE 1 Report — Workload Inference (Gate v1.3)

**Date:** 2026-06-03  
**Backend:** `local-gpu`  
**Methodology:** `phase1.4`  
**External claims:** BLOCKED until scale + held-out-model gates pass


> **PRELIMINARY** — Do not use in external writeups, applications, or Azure until gates in
> `docs/PRELIMINARY_CAVEATS.md` are satisfied (≥8 architectures, single-draw, held-out-model,
> hard-case detector). Phase 3 **not approved**.


## Gate summary

- **methodology:** phase1.4 — majority baseline, balanced accuracy + MI pass, balanced config subsample
- **external_fingerprint_claims:** BLOCKED
- **architecture_inference_headline:** BLOCKED — held-out-model and balanced multiclass inference fail
- **detector_headline:** hard_unauthorized_architecture + adaptive covert (not heavy AUC alone)
- **null_axes:** ['llm_phase', 'seq_length']
- **preliminary_real_axes:** ['mode', 'batch_size']
- **phase_3:** APPROVED (local mitigation) — external/Azure gated
- **llm_phase_null_rationale:** volume-confounded (total-bytes ablation ≈ 1.0) + minority-class fragility; NOT because metrics fail majority

## 0. Corpus (physical vs observation draws)


| Metric | Value |
|--------|--------|
| **Physical base captures** | **4576** |
| Stochastic observation draws | 183040 |
| Workload configs | 39 |

*'stochastic_observation_draws' are NOT additional GPU executions; only physical_base_captures are real local-gpu collects.*


## 0b. architecture_id vs model_class (labeling audit)


| Field | Value |
|-------|--------|
| Physical distinct `architecture_id` | **12** |
| Min for fingerprint claim | 8 |
| `model_class` | **RETRACTED** — do not cite in headline |
| `architecture_id` | **CANONICAL_PENDING_GATES** |

architecture_id vs model_class disagreement on legacy 2-arch corpus: model_class is a coarse bucket aligned with train/infer volume; architecture_id can track config bundles. Only architecture_id is canonical for fingerprint claims after >=8 physical architectures.

See `docs/architecture_labeling_audit.md`.


## 1. Observer aggregation (requirement #1)

| Report key | Interpretation |
|------------|----------------|
| `host_observer_realistic_single_draw` | **REALISTIC** — REALISTIC: one stochastic observer draw per physical base capture (observation_idx=0) |
| `host_observer_realistic_mean_draw` | **GENEROUS upper bound** — GENEROUS upper bound: mean of N stochastic observer draws per physical base capture |

### REALISTIC — single draw (headline for non-retracted axes)

### Single-draw realistic observer

| Axis | Bal.Acc | Maj.Base | Macro-F1 | MI | Bal.CI | PASS | Claim |
|------|---------|----------|----------|-----|--------|------|-------|
| mode | 1.000 | 0.604 | 1.000 | 0.693 | 1.000–1.000 | YES | PRELIMINARY_REAL |

Per-class recall: `{'infer': 1.0, 'train': 1.0}`


Confusion: `[[488, 0], [0, 488]]`

| model_class | 0.840 | 0.451 | 0.791 | 0.690 | 0.821–0.858 | NO | RETRACTED |

Per-class recall: `{'large': 0.9940476190476191, 'medium': 0.525, 'small': 1.0}`


*model_class:*  model_class confounded

Confusion: `[[167, 0, 1], [126, 168, 26], [0, 0, 320]]`

| architecture_id | 0.130 | 0.099 | 0.079 | 1.527 | 0.101–0.162 | NO | NEGATIVE |

Per-class recall: `{'arch_legacy_large': 0.5, 'arch_legacy_small': 0.0, 'arch_mlp_1024x8': 0.0, 'arch_mlp_1280x8': 0.0, 'arch_mlp_128x3': 0.0625, 'arch_mlp_1536x10': 0.0, 'arch_mlp_1920x10': 0.0, 'arch_mlp_2048x12': 1.0, 'arch_mlp_256x4': 0.0, 'arch_mlp_384x12': 0.0, 'arch_mlp_512x6': 0.0, 'arch_mlp_768x6': 0.0}`


*architecture_id:*  held-out-model FAIL

Confusion: `[[4, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0], [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 159], [10, 6, 129, 0, 10, 0, 0, 0, 0, 0, 5, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 0, 0, 0, 0, 0, 157, 0, 3, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [21, 2, 132, 0, 2, 0, 0, 0, 0, 0, 3, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 11, 0, 0, 0, 0, 0, 0, 0, 149, 0]]`

| batch_size | 0.500 | 0.328 | 0.414 | 0.633 | 0.500–0.500 | YES | PRELIMINARY_REAL |

Per-class recall: `{'1': 1.0, '2': 0.0, '4': 0.0, '8': 1.0}`


Confusion: `[[160, 0, 0, 0], [0, 0, 0, 8], [0, 0, 0, 160], [0, 0, 0, 160]]`

| seq_length | 0.255 | 0.476 | 0.173 | 0.083 | 0.250–0.261 | NO | NULL |

Per-class recall: `{'1024': 0.0, '128': 0.0, '256': 0.01875, '512': 1.0}`


*seq_length:* minority-class fragility (per-class support {'1024': 8, '128': 8, '256': 160, '512': 160}; classes with n<16: ['1024', '128']); balanced accuracy 0.255 does not beat majority baseline 0.476; MI 0.083 < 0.15 bits

Confusion: `[[0, 6, 0, 2], [0, 0, 0, 8], [0, 0, 3, 157], [0, 0, 0, 160]]`

| llm_phase | 1.000 | 0.333 | 1.000 | 0.368 | 1.000–1.000 | NO | NULL |

Per-class recall: `{'decode': 1.0, 'n/a': 1.0, 'prefill': 1.0}`


*llm_phase:* Coarse volume leakage: total-bytes ablation within 5% of full realistic features.; minority-class fragility (per-class support {'decode': 8, 'n/a': 160, 'prefill': 8}; classes with n<16: ['decode', 'prefill']); metrics beat majority and pass MI floor but axis is not claimable (confound / fragility — not a fine-grained channel)

Confusion: `[[8, 0, 0], [0, 160, 0], [0, 0, 8]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Bal.Acc | Maj.Base | Macro-F1 | MI | Bal.CI | PASS | Claim |
|------|---------|----------|----------|-----|--------|------|-------|
| mode | 1.000 | 0.604 | 1.000 | 0.693 | 1.000–1.000 | YES | PRELIMINARY_REAL |

Per-class recall: `{'infer': 1.0, 'train': 1.0}`


Confusion: `[[488, 0], [0, 488]]`

| model_class | 0.833 | 0.451 | 0.781 | 0.756 | 0.813–0.852 | NO | RETRACTED |

Per-class recall: `{'large': 1.0, 'medium': 0.5, 'small': 1.0}`


*model_class:*  model_class confounded

Confusion: `[[168, 0, 0], [156, 160, 4], [0, 0, 320]]`

| architecture_id | 0.083 | 0.099 | 0.056 | 1.355 | 0.083–0.083 | NO | NEGATIVE |

Per-class recall: `{'arch_legacy_large': 0.0, 'arch_legacy_small': 0.0, 'arch_mlp_1024x8': 0.0, 'arch_mlp_1280x8': 0.0, 'arch_mlp_128x3': 0.0, 'arch_mlp_1536x10': 0.0, 'arch_mlp_1920x10': 0.0, 'arch_mlp_2048x12': 1.0, 'arch_mlp_256x4': 0.0, 'arch_mlp_384x12': 0.0, 'arch_mlp_512x6': 0.0, 'arch_mlp_768x6': 0.0}`


*architecture_id:*  held-out-model FAIL

Confusion: `[[0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0], [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [156, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [153, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 156, 0]]`

| batch_size | 0.500 | 0.328 | 0.414 | 0.633 | 0.500–0.500 | YES | PRELIMINARY_REAL |

Per-class recall: `{'1': 1.0, '2': 0.0, '4': 0.0, '8': 1.0}`


Confusion: `[[160, 0, 0, 0], [0, 0, 0, 8], [0, 0, 0, 160], [0, 0, 0, 160]]`

| seq_length | 0.250 | 0.476 | 0.164 | 0.113 | 0.250–0.250 | NO | NULL |

Per-class recall: `{'1024': 0.0, '128': 0.0, '256': 0.0, '512': 1.0}`


*seq_length:* minority-class fragility (per-class support {'1024': 8, '128': 8, '256': 160, '512': 160}; classes with n<16: ['1024', '128']); balanced accuracy 0.250 does not beat majority baseline 0.476; MI 0.113 < 0.15 bits

Confusion: `[[0, 8, 0, 0], [0, 0, 0, 8], [0, 0, 0, 160], [0, 0, 0, 160]]`

| llm_phase | 1.000 | 0.333 | 1.000 | 0.368 | 1.000–1.000 | NO | NULL |

Per-class recall: `{'decode': 1.0, 'n/a': 1.0, 'prefill': 1.0}`


*llm_phase:* Coarse volume leakage: total-bytes ablation within 5% of full realistic features.; minority-class fragility (per-class support {'decode': 8, 'n/a': 160, 'prefill': 8}; classes with n<16: ['decode', 'prefill']); metrics beat majority and pass MI floor but axis is not claimable (confound / fragility — not a fine-grained channel)

Confusion: `[[8, 0, 0], [0, 160, 0], [0, 0, 8]]`



## 2. Held-out-model validation (requirement #2)

**Gate status:** PRELIMINARY — interpret held-out accuracy; no external fingerprint claim until PASS  
**Physical architectures in corpus:** 12  
Split: entire architecture_id held out of train; test rows are only unseen architectures (single-draw realistic observer)  
Aggregation: `single_draw`  

**architecture_id** — held out `['arch_legacy_large', 'arch_mlp_2048x12', 'arch_mlp_1920x10']`; train archs `['arch_legacy_small', 'arch_mlp_1024x8', 'arch_mlp_1280x8', 'arch_mlp_128x3', 'arch_mlp_1536x10', 'arch_mlp_256x4', 'arch_mlp_384x12', 'arch_mlp_512x6', 'arch_mlp_768x6']`; acc=0.000, PASS=False; NEGATIVE: held-out-model does not generalize — honest bounding result

**model_class** — held out `['arch_legacy_large', 'arch_mlp_2048x12', 'arch_mlp_1920x10']`; train archs `['arch_legacy_small', 'arch_mlp_1024x8', 'arch_mlp_1280x8', 'arch_mlp_128x3', 'arch_mlp_1536x10', 'arch_mlp_256x4', 'arch_mlp_384x12', 'arch_mlp_512x6', 'arch_mlp_768x6']`; acc=0.000, PASS=False; NEGATIVE: test fold has a single class (holdout did not include all label values) RETRACTED: model_class not reported as fingerprint result


Do **not** claim model fingerprinting unless `architecture_id` held-out-model passes with ≥8 physical architectures.

## 3. Ablation (volume only)

### Total bytes ablation

| Axis | Bal.Acc | Maj.Base | Macro-F1 | MI | Bal.CI | PASS | Claim |
|------|---------|----------|----------|-----|--------|------|-------|
| mode | 1.000 | 0.604 | 1.000 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Per-class recall: `{'infer': 1.0, 'train': 1.0}`


Confusion: `[[488, 0], [0, 488]]`

| model_class | 0.984 | 0.451 | 0.988 | 1.014 | 0.972–0.994 | YES | PRELIMINARY |

Per-class recall: `{'large': 0.9523809523809523, 'medium': 1.0, 'small': 1.0}`


Confusion: `[[160, 8, 0], [0, 320, 0], [0, 0, 320]]`

| architecture_id | 0.083 | 0.099 | 0.056 | 1.492 | 0.083–0.083 | NO | PRELIMINARY |

Per-class recall: `{'arch_legacy_large': 0.0, 'arch_legacy_small': 0.0, 'arch_mlp_1024x8': 0.0, 'arch_mlp_1280x8': 0.0, 'arch_mlp_128x3': 0.0, 'arch_mlp_1536x10': 0.0, 'arch_mlp_1920x10': 0.0, 'arch_mlp_2048x12': 1.0, 'arch_mlp_256x4': 0.0, 'arch_mlp_384x12': 0.0, 'arch_mlp_512x6': 0.0, 'arch_mlp_768x6': 0.0}`


Confusion: `[[0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0], [0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0]]`

| batch_size | 0.250 | 0.328 | 0.167 | 0.644 | 0.250–0.250 | NO | PRELIMINARY |

Per-class recall: `{'1': 1.0, '2': 0.0, '4': 0.0, '8': 0.0}`


Confusion: `[[160, 0, 0, 0], [0, 0, 0, 8], [0, 0, 0, 160], [160, 0, 0, 0]]`

| seq_length | 0.250 | 0.476 | 0.238 | 0.692 | 0.250–0.250 | NO | PRELIMINARY |

Per-class recall: `{'1024': 0.0, '128': 0.0, '256': 0.0, '512': 1.0}`


Confusion: `[[0, 0, 0, 8], [0, 0, 0, 8], [160, 0, 0, 0], [0, 0, 0, 160]]`

| llm_phase | 1.000 | 0.333 | 1.000 | 0.368 | 1.000–1.000 | YES | PRELIMINARY |

Per-class recall: `{'decode': 1.0, 'n/a': 1.0, 'prefill': 1.0}`


Confusion: `[[8, 0, 0], [0, 160, 0], [0, 0, 8]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Volume channel dominates; fine-grained claim not supported.
- **llm_phase:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Bal.Acc | Maj.Base | Macro-F1 | MI | Bal.CI | PASS | Claim |
|------|---------|----------|----------|-----|--------|------|-------|
| mode | 1.000 | 0.604 | 1.000 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Per-class recall: `{'infer': 1.0, 'train': 1.0}`


Confusion: `[[488, 0], [0, 488]]`

| model_class | 0.832 | 0.451 | 0.780 | 0.771 | 0.812–0.851 | YES | PRELIMINARY |

Per-class recall: `{'large': 1.0, 'medium': 0.5, 'small': 0.996875}`


Confusion: `[[168, 0, 0], [160, 160, 0], [1, 0, 319]]`

| architecture_id | 0.167 | 0.099 | 0.139 | 1.501 | 0.167–0.167 | YES | PRELIMINARY |

Per-class recall: `{'arch_legacy_large': 0.0, 'arch_legacy_small': 0.0, 'arch_mlp_1024x8': 0.0, 'arch_mlp_1280x8': 0.0, 'arch_mlp_128x3': 0.0, 'arch_mlp_1536x10': 1.0, 'arch_mlp_1920x10': 0.0, 'arch_mlp_2048x12': 1.0, 'arch_mlp_256x4': 0.0, 'arch_mlp_384x12': 0.0, 'arch_mlp_512x6': 0.0, 'arch_mlp_768x6': 0.0}`


Confusion: `[[0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0], [7, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 157, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [122, 0, 0, 21, 0, 0, 0, 0, 0, 0, 17, 0], [0, 0, 0, 0, 53, 0, 0, 0, 0, 0, 107, 0], [0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 151], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0]]`

| batch_size | 0.500 | 0.328 | 0.414 | 0.633 | 0.500–0.500 | YES | PRELIMINARY |

Per-class recall: `{'1': 1.0, '2': 0.0, '4': 0.0, '8': 1.0}`


Confusion: `[[160, 0, 0, 0], [0, 0, 0, 8], [0, 0, 0, 160], [0, 0, 0, 160]]`

| seq_length | 0.500 | 0.476 | 0.494 | 0.789 | 0.500–0.500 | YES | PRELIMINARY |

Per-class recall: `{'1024': 0.0, '128': 0.0, '256': 1.0, '512': 1.0}`


Confusion: `[[0, 8, 0, 0], [0, 0, 0, 8], [0, 0, 160, 0], [0, 0, 0, 160]]`

| llm_phase | 0.750 | 0.333 | 0.709 | 0.313 | 0.667–0.889 | YES | PRELIMINARY |

Per-class recall: `{'decode': 0.25, 'n/a': 1.0, 'prefill': 1.0}`


Confusion: `[[2, 0, 6], [0, 160, 0], [0, 0, 8]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Re-collect on **10-architecture** corpus, then re-run evaluate + detect. Phase 3 blocked.
