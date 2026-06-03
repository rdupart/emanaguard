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
| **Physical base captures** | **96** |
| Stochastic observation draws | 3840 |
| Workload configs | 12 |

*'stochastic_observation_draws' are NOT additional GPU executions; only physical_base_captures are real local-gpu collects.*


## 0b. architecture_id vs model_class (labeling audit)


| Field | Value |
|-------|--------|
| Physical distinct `architecture_id` | **2** |
| Min for fingerprint claim | 8 |
| `model_class` | **RETRACTED** — do not cite in headline |
| `architecture_id` | **RETRACTED_INSUFFICIENT_CORPUS** |

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
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[8, 0], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | NO | RETRACTED_INSUFFICIENT_CORPUS |

*architecture_id:* only 2 physical architectures (need >=8); collect expanded corpus

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.469 | 0.250 | 0.500 | 0.281–0.625 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0, 0], [0, 0, 8, 0], [1, 0, 7, 0], [0, 0, 8, 0]]`

| seq_length | 0.500 | 0.250 | 0.931 | 0.344–0.656 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 0, 8], [6, 2, 0, 0]]`

| llm_phase | 0.562 | 0.333 | 0.089 | 0.375–0.750 | YES | PRELIMINARY |

Confusion: `[[1, 7, 0], [0, 16, 0], [0, 7, 1]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | NO | RETRACTED |

*model_class:* model_class confounded with mode/volume — see docs/architecture_labeling_audit.md

Confusion: `[[8, 0], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | NO | RETRACTED_INSUFFICIENT_CORPUS |

*architecture_id:* only 2 physical architectures (need >=8); collect expanded corpus

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.438 | 0.250 | 0.374 | 0.281–0.625 | YES | PRELIMINARY |

Confusion: `[[7, 0, 1, 0], [0, 0, 8, 0], [1, 0, 7, 0], [0, 0, 8, 0]]`

| seq_length | 0.438 | 0.250 | 1.097 | 0.280–0.625 | YES | PRELIMINARY |

Confusion: `[[5, 0, 3, 0], [0, 8, 0, 0], [0, 0, 0, 8], [0, 0, 7, 1]]`

| llm_phase | 0.812 | 0.333 | 0.637 | 0.656–0.938 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 16, 0], [0, 6, 2]]`



## 2. Held-out-model validation (requirement #2)

**Gate status:** BLOCKED: only 2 physical architectures; need >=8 after collect on expanded corpus  
**Physical architectures in corpus:** 2  
Split: entire architecture_id held out of train; test rows are only unseen architectures (single-draw realistic observer)  
Aggregation: `single_draw`  

**architecture_id** — held out `['arch_legacy_small']`; train archs `['arch_legacy_large']`; acc=0.000, PASS=False; NEGATIVE: train fold has a single class RETRACTED: <8 architectures in corpus

**model_class** — held out `['arch_legacy_small']`; train archs `['arch_legacy_large']`; acc=0.000, PASS=False; NEGATIVE: train fold has a single class RETRACTED: model_class not reported as fingerprint result


Do **not** claim model fingerprinting unless `architecture_id` held-out-model passes with ≥8 physical architectures.

## 3. Ablation (volume only)

### Total bytes ablation

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 0.500 | 0.500 | 0.000 | 0.250–0.750 | NO | PRELIMINARY |

Confusion: `[[0, 8], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.281 | 0.250 | 0.045 | 0.125–0.438 | NO | PRELIMINARY |

Confusion: `[[1, 0, 7, 0], [0, 0, 8, 0], [0, 0, 8, 0], [0, 0, 8, 0]]`

| seq_length | 0.250 | 0.250 | 0.000 | 0.094–0.406 | NO | PRELIMINARY |

Confusion: `[[0, 0, 0, 8], [0, 0, 0, 8], [0, 0, 0, 8], [0, 0, 0, 8]]`

| llm_phase | 0.750 | 0.333 | 0.693 | 0.594–0.906 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0], [0, 8, 8], [0, 0, 8]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **architecture_id:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |
|------|-----|--------|-----|------------|------|-------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | PRELIMINARY |

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.469 | 0.250 | 0.500 | 0.281–0.625 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0, 0], [0, 0, 8, 0], [1, 0, 7, 0], [0, 0, 8, 0]]`

| seq_length | 0.531 | 0.250 | 0.964 | 0.344–0.688 | YES | PRELIMINARY |

Confusion: `[[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 0, 8], [7, 0, 0, 1]]`

| llm_phase | 0.500 | 0.333 | 0.000 | 0.312–0.688 | NO | PRELIMINARY |

Confusion: `[[0, 8, 0], [0, 16, 0], [0, 8, 0]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Re-collect on **10-architecture** corpus, then re-run evaluate + detect. Phase 3 blocked.
