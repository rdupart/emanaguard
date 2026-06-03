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
| mode | 1.000 | 0.500 | 0.683 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[648, 0], [0, 488]]`

| model_class | 0.859 | 0.333 | 0.810 | 0.838–0.880 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[488, 0, 0], [0, 320, 0], [0, 160, 168]]`

| architecture_id | 0.008 | 0.083 | 2.120 | 0.004–0.012 | NO | PRELIMINARY_PENDING_HELD_OUT |

Confusion: `[[7, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 6, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0], [0, 77, 0, 0, 83, 0, 0, 0, 0, 0, 0, 0], [0, 0, 21, 0, 0, 139, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 153, 0]]`

| batch_size | 0.952 | 0.250 | 0.671 | 0.940–0.964 | YES | PRELIMINARY |

Confusion: `[[647, 0, 0, 1], [0, 0, 8, 0], [2, 0, 450, 36], [0, 0, 8, 0]]`

| seq_length | 0.993 | 0.250 | 0.478 | 0.989–0.997 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 960, 0, 0], [0, 0, 160, 0], [0, 0, 0, 8]]`

| llm_phase | 0.999 | 0.333 | 0.484 | 0.997–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 815, 1], [0, 0, 160]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.683 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[648, 0], [0, 488]]`

| model_class | 0.859 | 0.333 | 0.810 | 0.838–0.880 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[488, 0, 0], [0, 320, 0], [0, 160, 168]]`

| architecture_id | 0.006 | 0.083 | 2.181 | 0.002–0.010 | NO | PRELIMINARY_PENDING_HELD_OUT |

Confusion: `[[8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0, 0, 0, 5, 0, 1, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0], [0, 146, 0, 0, 14, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 159, 0]]`

| batch_size | 0.970 | 0.250 | 0.674 | 0.959–0.979 | YES | PRELIMINARY |

Confusion: `[[648, 0, 0, 0], [0, 0, 8, 0], [2, 0, 469, 17], [0, 0, 8, 0]]`

| seq_length | 0.993 | 0.250 | 0.478 | 0.989–0.997 | YES | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 960, 0, 0], [0, 0, 160, 0], [0, 0, 0, 8]]`

| llm_phase | 1.000 | 0.333 | 0.490 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 816, 0], [0, 0, 160]]`



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
| mode | 1.000 | 0.500 | 0.683 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[648, 0], [0, 488]]`

| model_class | 0.859 | 0.333 | 0.810 | 0.838–0.880 | YES | PRELIMINARY |

Confusion: `[[488, 0, 0], [0, 320, 0], [0, 160, 168]]`

| architecture_id | 0.000 | 0.083 | 2.173 | 0.000–0.000 | NO | PRELIMINARY |

Confusion: `[[0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0], [0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0], [0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 0, 10, 0, 149], [158, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0]]`

| batch_size | 0.847 | 0.250 | 0.342 | 0.827–0.868 | YES | PRELIMINARY |

Confusion: `[[648, 0, 0, 0], [0, 0, 8, 0], [160, 0, 328, 0], [0, 0, 8, 0]]`

| seq_length | 0.993 | 0.250 | 0.447 | 0.989–0.997 | YES | PRELIMINARY |

Confusion: `[[0, 8, 0, 0], [0, 960, 0, 0], [0, 0, 160, 0], [0, 0, 0, 8]]`

| llm_phase | 0.667 | 0.333 | 0.448 | 0.637–0.695 | YES | PRELIMINARY |

Confusion: `[[0, 8, 0], [320, 496, 0], [0, 0, 160]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Volume channel dominates; fine-grained claim not supported.
- **seq_length:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.683 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[648, 0], [0, 488]]`

| model_class | 0.859 | 0.333 | 0.810 | 0.838–0.880 | YES | PRELIMINARY |

Confusion: `[[488, 0, 0], [0, 320, 0], [0, 160, 168]]`

| architecture_id | 0.000 | 0.083 | 2.130 | 0.000–0.000 | NO | PRELIMINARY |

Confusion: `[[0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0], [7, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 69, 0, 0, 0, 0, 0, 0, 91, 0], [0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0], [0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0], [0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 160, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 160, 0]]`

| batch_size | 0.984 | 0.250 | 0.674 | 0.977–0.991 | YES | PRELIMINARY |

Confusion: `[[648, 0, 0, 0], [0, 0, 8, 0], [2, 0, 486, 0], [0, 0, 8, 0]]`

| seq_length | 1.000 | 0.250 | 0.488 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0, 0], [0, 960, 0, 0], [0, 0, 160, 0], [0, 0, 0, 8]]`

| llm_phase | 0.990 | 0.333 | 0.443 | 0.983–0.996 | YES | PRELIMINARY |

Confusion: `[[0, 0, 8], [0, 816, 0], [0, 2, 158]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Re-collect on **10-architecture** corpus, then re-run evaluate + detect. Phase 3 blocked.
