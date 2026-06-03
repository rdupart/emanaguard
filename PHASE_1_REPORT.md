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
| **Physical base captures** | **2016** |
| Stochastic observation draws | 80640 |
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
| mode | 0.996 | 0.500 | 0.612 | 0.990–1.000 | YES |

Confusion: `[[336, 0], [2, 166]]`

| model_class | 0.500 | 0.500 | 0.000 | 0.446–0.554 | NO |

Confusion: `[[0, 168], [0, 168]]`

| architecture_id | 0.946 | 0.500 | 0.517 | 0.920–0.967 | YES |

Confusion: `[[150, 18], [0, 168]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.217–0.283 | NO |

Confusion: `[[168, 0, 0, 0], [168, 0, 0, 0], [168, 0, 0, 0], [0, 0, 168, 0]]`

| seq_length | 0.250 | 0.250 | 0.527 | 0.219–0.284 | NO |

Confusion: `[[0, 160, 0, 8], [0, 168, 0, 0], [0, 0, 0, 168], [0, 168, 0, 0]]`

| llm_phase | 0.999 | 0.333 | 1.030 | 0.996–1.000 | YES |

Confusion: `[[167, 1, 0], [0, 336, 0], [0, 0, 168]]`



### GENEROUS — mean of 40 draws (upper bound)

### Mean-draw realistic observer

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.996 | 0.500 | 0.612 | 0.990–1.000 | YES |

Confusion: `[[336, 0], [2, 166]]`

| model_class | 0.500 | 0.500 | 0.000 | 0.446–0.554 | NO |

Confusion: `[[0, 168], [0, 168]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[168, 0], [0, 168]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.217–0.283 | NO |

Confusion: `[[168, 0, 0, 0], [168, 0, 0, 0], [168, 0, 0, 0], [0, 0, 168, 0]]`

| seq_length | 0.250 | 0.250 | 0.562 | 0.219–0.284 | NO |

Confusion: `[[0, 168, 0, 0], [0, 168, 0, 0], [0, 0, 0, 168], [0, 168, 0, 0]]`

| llm_phase | 0.783 | 0.333 | 0.600 | 0.753–0.814 | YES |

Confusion: `[[22, 146, 0], [0, 336, 0], [0, 0, 168]]`



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

Confusion: `[[336, 0], [0, 168]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[168, 0], [0, 168]]`

| architecture_id | 0.500 | 0.500 | 0.000 | 0.446–0.554 | NO |

Confusion: `[[0, 168], [0, 168]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.217–0.283 | NO |

Confusion: `[[168, 0, 0, 0], [168, 0, 0, 0], [168, 0, 0, 0], [0, 0, 168, 0]]`

| seq_length | 0.250 | 0.250 | 0.562 | 0.219–0.284 | NO |

Confusion: `[[0, 168, 0, 0], [0, 168, 0, 0], [0, 0, 0, 168], [0, 168, 0, 0]]`

| llm_phase | 0.747 | 0.333 | 0.679 | 0.713–0.778 | YES |

Confusion: `[[168, 0, 0], [0, 168, 168], [0, 2, 166]]`



- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Volume channel dominates; fine-grained claim not supported.

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

### Idealized

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.996 | 0.500 | 0.612 | 0.990–1.000 | YES |

Confusion: `[[336, 0], [2, 166]]`

| model_class | 0.976 | 0.500 | 0.596 | 0.958–0.991 | YES |

Confusion: `[[160, 8], [0, 168]]`

| architecture_id | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES |

Confusion: `[[168, 0], [0, 168]]`

| batch_size | 0.250 | 0.250 | 0.562 | 0.217–0.283 | NO |

Confusion: `[[168, 0, 0, 0], [168, 0, 0, 0], [168, 0, 0, 0], [0, 0, 168, 0]]`

| seq_length | 0.250 | 0.250 | 0.693 | 0.219–0.284 | NO |

Confusion: `[[0, 0, 0, 168], [0, 168, 0, 0], [0, 0, 0, 168], [0, 168, 0, 0]]`

| llm_phase | 0.750 | 0.333 | 0.562 | 0.717–0.781 | YES |

Confusion: `[[0, 168, 0], [0, 336, 0], [0, 0, 168]]`



## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Phase 2 approved in parallel; detector inherits preliminary caveat.
