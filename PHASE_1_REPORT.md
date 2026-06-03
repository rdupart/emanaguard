# PHASE 1 Report — Workload Inference (Gate v1.3)

**Date:** 2026-06-03  
**Backend:** `local-gpu`  
**Methodology:** `phase1.3`  
**External claims:** BLOCKED until scale + held-out-model gates pass


> **PRELIMINARY** — Do not use in external writeups, applications, or Azure until gates in
> `docs/PRELIMINARY_CAVEATS.md` are satisfied (single-draw reporting, held-out-model, physical scale).


## 0. Corpus (physical vs observation draws)


| Metric | Value |
|--------|--------|
| **Physical base captures** | **96** |
| Stochastic observation draws | 3840 |
| Workload configs | 12 |

*'stochastic_observation_draws' are NOT additional GPU executions; only physical_base_captures are real local-gpu collects.*


## 1. Observer aggregation (requirement #1)

| Report key | Interpretation |
|------------|----------------|
| `host_observer_realistic_single_draw` | **REALISTIC** — REALISTIC: one stochastic observer draw per physical base capture (observation_idx=0) |
| `host_observer_realistic_mean_draw` | **GENEROUS upper bound** — GENEROUS upper bound: mean of N stochastic observer draws per physical base capture |

### REALISTIC — single draw (headline for claims)

### Single-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 0.500 | 0.500 | 0.000 | 0.250–0.750 | NO |

Confusion: `[[0, 8], [0, 8]]`

| architecture_id | 0.938 | 0.500 | 0.497 | 0.812–1.000 | YES |

Confusion: `[[7, 1], [0, 8]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.094–0.406 | NO |

Confusion: `[[8, 0, 0, 0], [8, 0, 0, 0], [8, 0, 0, 0], [0, 0, 8, 0]]`

| seq_length | 0.625 | 0.250 | 0.781 | 0.469–0.781 | YES |

Confusion: `[[4, 0, 3, 1], [0, 8, 0, 0], [0, 0, 8, 0], [0, 0, 8, 0]]`

| llm_phase | 0.625 | 0.333 | 0.696 | 0.469–0.781 | YES |

Confusion: `[[0, 1, 7], [0, 16, 0], [4, 0, 4]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 0.500 | 0.500 | 0.000 | 0.250–0.750 | NO |

Confusion: `[[0, 8], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.094–0.406 | NO |

Confusion: `[[8, 0, 0, 0], [8, 0, 0, 0], [8, 0, 0, 0], [0, 0, 8, 0]]`

| seq_length | 0.750 | 0.250 | 1.040 | 0.594–0.906 | YES |

Confusion: `[[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 8, 0], [0, 0, 8, 0]]`

| llm_phase | 0.750 | 0.333 | 0.562 | 0.594–0.906 | YES |

Confusion: `[[0, 8, 0], [0, 16, 0], [0, 0, 8]]`



## 2. Held-out-model validation (requirement #2)

Split: entire architecture_id held out of train; test contains only unseen models  
Aggregation: `single_draw`  

**architecture_id** (held-out architectures `['arch_legacy_small']`): acc=0.000, PASS=False, NEGATIVE: train fold has a single class held_out_model_split

**model_class** (held-out architectures `['arch_legacy_small']`): acc=0.000, PASS=False, NEGATIVE: train fold has a single class held_out_model_split


## 3. Ablation (volume only)

### Total bytes ablation

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[8, 0], [0, 8]]`

| architecture_id | 0.500 | 0.500 | 0.000 | 0.250–0.750 | NO |

Confusion: `[[0, 8], [0, 8]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.094–0.406 | NO |

Confusion: `[[8, 0, 0, 0], [8, 0, 0, 0], [8, 0, 0, 0], [0, 0, 8, 0]]`

| seq_length | 0.000 | 0.250 | 0.693 | 0.000–0.000 | NO |

Confusion: `[[0, 0, 0, 8], [0, 0, 0, 8], [8, 0, 0, 0], [8, 0, 0, 0]]`

| llm_phase | 0.250 | 0.333 | 0.216 | 0.094–0.406 | NO |

Confusion: `[[0, 0, 8], [8, 0, 8], [0, 0, 8]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Volume channel dominates; fine-grained claim not supported.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion: `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[8, 0], [0, 8]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[8, 0], [0, 8]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.094–0.406 | NO |

Confusion: `[[8, 0, 0, 0], [8, 0, 0, 0], [8, 0, 0, 0], [0, 0, 8, 0]]`

| seq_length | 0.750 | 0.250 | 1.040 | 0.594–0.906 | YES |

Confusion: `[[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 8, 0], [0, 0, 8, 0]]`

| llm_phase | 0.750 | 0.333 | 0.562 | 0.594–0.906 | YES |

Confusion: `[[0, 8, 0], [0, 16, 0], [0, 0, 8]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Phase 2 approved in parallel; detector inherits preliminary caveat.
