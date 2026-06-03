# PHASE 1 Report — Workload Inference (Gate v1.3)

**Date:** 2026-06-03  
**Backend:** `local-gpu`  
**Methodology:** `phase1.3`  
**External claims:** BLOCKED until scale + held-out-model gates pass


> **PRELIMINARY** — Do not use in external writeups, applications, or Azure until gates in
> `docs/PRELIMINARY_CAVEATS.md` are satisfied (≥8 architectures, single-draw, held-out-model,
> hard-case detector). Phase 3 **not approved**.


## Gate summary

- **external_fingerprint_claims:** BLOCKED
- **architecture_inference_headline:** BLOCKED until >=8 physical architectures and held-out-model PASS on architecture_id
- **detector_headline:** Phase 2 hard suites only (not trivial mode-change AUC)
- **phase_3:** NOT_APPROVED — re-collect on 10-arch corpus then re-run gates

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

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 0.998 | 0.500 | 0.680 | 0.995–1.000 | YES | PRELIMINARY |

Confusion: `[[496, 0], [2, 494]]`

| model_class | 0.842 | 0.333 | 0.660 | 0.820–0.863 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[416, 72, 0], [0, 301, 19], [0, 88, 240]]`

| architecture_id | 0.040 | 0.083 | 1.666 | 0.030–0.050 | NO | PRELIMINARY_PENDING_HELD_OUT |

Confusion: `[[7, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], [0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 154], [0, 0, 0, 0, 0, 102, 0, 0, 0, 0, 0, 58], [0, 4, 0, 0, 1, 0, 0, 0, 155, 0, 0, 0], [0, 0, 0, 153, 0, 0, 7, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0], [0, 0, 112, 0, 0, 0, 0, 0, 0, 48, 0, 0], [0, 0, 38, 0, 23, 0, 0, 0, 0, 99, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0]]`

| batch_size | 0.963 | 0.250 | 0.998 | 0.950–0.975 | YES | PRELIMINARY |

Confusion: `[[331, 13, 0, 0], [8, 0, 0, 0], [1, 2, 318, 7], [0, 0, 0, 160]]`

| seq_length | 0.863 | 0.250 | 0.122 | 0.837–0.887 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 587, 67, 2], [0, 8, 0, 0], [8, 0, 0, 0]]`

| llm_phase | 0.998 | 0.333 | 0.102 | 0.994–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 822, 2], [0, 0, 8]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 0.998 | 0.500 | 0.680 | 0.995–1.000 | YES | PRELIMINARY |

Confusion: `[[496, 0], [2, 494]]`

| model_class | 0.889 | 0.333 | 0.787 | 0.870–0.908 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[461, 27, 0], [0, 320, 0], [0, 99, 229]]`

| architecture_id | 0.109 | 0.083 | 1.849 | 0.094–0.124 | YES | PRELIMINARY_PENDING_HELD_OUT |

Confusion: `[[8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 152], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 3, 0, 0, 0, 0, 0, 0, 157, 0, 0, 0], [0, 0, 0, 24, 0, 0, 136, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0]]`

| batch_size | 0.971 | 0.250 | 1.009 | 0.960–0.982 | YES | PRELIMINARY |

Confusion: `[[336, 8, 0, 0], [8, 0, 0, 0], [0, 0, 320, 8], [0, 0, 0, 160]]`

| seq_length | 0.891 | 0.250 | 0.066 | 0.866–0.915 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 606, 50, 0], [0, 8, 0, 0], [0, 8, 0, 0]]`

| llm_phase | 0.998 | 0.333 | 0.102 | 0.994–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 822, 2], [0, 0, 8]]`



## 2. Held-out-model validation (requirement #2)

**Gate status:** PRELIMINARY — interpret held-out accuracy; no external fingerprint claim until PASS  
**Physical architectures in corpus:** 12  
Split: entire architecture_id held out of train; test rows are only unseen architectures (single-draw realistic observer)  
Aggregation: `single_draw`  

**architecture_id** — held out `['arch_legacy_large', 'arch_mlp_2048x12', 'arch_mlp_1920x10']`; train archs `['arch_legacy_small', 'arch_mlp_1024x8', 'arch_mlp_1280x8', 'arch_mlp_128x3', 'arch_mlp_1536x10', 'arch_mlp_256x4', 'arch_mlp_384x12', 'arch_mlp_512x6', 'arch_mlp_768x6']`; acc=0.000, PASS=False; NEGATIVE: held-out-model does not generalize — honest bounding result

**model_class** — held out `['arch_legacy_large', 'arch_mlp_2048x12', 'arch_mlp_1920x10']`; train archs `['arch_legacy_small', 'arch_mlp_1024x8', 'arch_mlp_1280x8', 'arch_mlp_128x3', 'arch_mlp_1536x10', 'arch_mlp_256x4', 'arch_mlp_384x12', 'arch_mlp_512x6', 'arch_mlp_768x6']`; acc=1.000, PASS=False; NEGATIVE: test fold has a single class (holdout did not include all label values) RETRACTED: model_class not reported as fingerprint result


Do **not** claim model fingerprinting unless `architecture_id` held-out-model passes with ≥8 physical architectures.

## 3. Ablation (volume only)

### Total bytes ablation

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[496, 0], [0, 496]]`

| model_class | 0.716 | 0.333 | 0.668 | 0.689–0.744 | YES | PRELIMINARY |

Confusion: `[[485, 3, 0], [0, 160, 160], [0, 160, 168]]`

| architecture_id | 0.000 | 0.083 | 2.030 | 0.000–0.000 | NO | PRELIMINARY |

Confusion: `[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8], [0, 0, 0, 0, 1, 0, 0, 0, 7, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [160, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0], [0, 0, 0, 91, 0, 0, 69, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0]]`

| batch_size | 0.790 | 0.250 | 1.002 | 0.764–0.817 | YES | PRELIMINARY |

Confusion: `[[344, 0, 0, 0], [8, 0, 0, 0], [8, 160, 160, 0], [0, 0, 0, 160]]`

| seq_length | 0.482 | 0.250 | 0.080 | 0.449–0.518 | YES | PRELIMINARY |

Confusion: `[[0, 8, 0, 0], [0, 328, 0, 328], [0, 8, 0, 0], [8, 0, 0, 0]]`

| llm_phase | 0.790 | 0.333 | 0.068 | 0.762–0.819 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [176, 648, 0], [0, 0, 8]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[496, 0], [0, 496]]`

| model_class | 0.570 | 0.333 | 0.329 | 0.544–0.598 | YES | PRELIMINARY |

Confusion: `[[160, 328, 0], [0, 320, 0], [0, 160, 168]]`

| architecture_id | 0.104 | 0.083 | 1.874 | 0.090–0.119 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0], [0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 1, 0, 0, 0, 0, 0, 0, 158, 0, 0, 1], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0], [0, 0, 99, 0, 0, 0, 0, 0, 0, 61, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0]]`

| batch_size | 0.981 | 0.250 | 1.002 | 0.971–0.989 | YES | PRELIMINARY |

Confusion: `[[344, 0, 0, 0], [8, 0, 0, 0], [8, 0, 320, 0], [0, 0, 0, 160]]`

| seq_length | 0.953 | 0.250 | 0.064 | 0.937–0.968 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 648, 8, 0], [0, 8, 0, 0], [0, 8, 0, 0]]`

| llm_phase | 0.998 | 0.333 | 0.102 | 0.994–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 822, 2], [0, 0, 8]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Re-collect on **10-architecture** corpus, then re-run evaluate + detect. Phase 3 blocked.
