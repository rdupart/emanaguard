# PHASE 1 Report — Workload Inference (Gate)

**Date:** 2026-06-03  
**Backend for all metrics below:** `local-gpu`  
**Headline signal set:** **(b) host_observer** (and sequence variant)

## 1. Observer validity (binding #1)

| Set | Definition | Headline? |
|-----|------------|-----------|
| **(a) `vm_ground_truth`** | In-VM features including `op_name`, `phase`, `stream` — see `pipeline/features/vm_ground_truth.py` | **No** — labels + upper bound only |
| **(b) `host_observer`** | Timing, size, direction, count, cadence — see `pipeline/features/host_observer.py` | **Yes** |

**Proxy disclaimer:** All **(b)** numbers below were collected on **`local-gpu` (non-CC)**. This is a **proxy/upper-bound** for the true malicious-host vantage under H100 CC-On. **Phase 4 (`azure-cc`)** must confirm ranking and magnitudes. **Do not conflate (a) and (b).**

## 2. Headline results — (b) host_observer

### Tabular (logistic regression on aggregate features)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS (lo>chance) | Backend |
|------|-----|--------|-----|------------|------------------|---------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (mode): `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (model_class): `[[12, 0], [0, 12]]`

| batch_size | 0.917 | 0.250 | 1.011 | 0.792–1.000 | YES | local-gpu |

Confusion matrix (batch_size): `[[10, 0, 2, 0], [0, 4, 0, 0], [0, 0, 6, 0], [0, 0, 0, 2]]`

| seq_length | 1.000 | 0.250 | 1.309 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (seq_length): `[[4, 0, 0, 0], [0, 10, 0, 0], [0, 0, 4, 0], [0, 0, 0, 6]]`

| llm_phase | 1.000 | 0.333 | 0.868 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (llm_phase): `[[4, 0, 0], [0, 16, 0], [0, 0, 4]]`



### Sequence model (MLP on size-bucket sequence)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS (lo>chance) | Backend |
|------|-----|--------|-----|------------|------------------|---------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (mode): `[[16, 0], [0, 8]]`

| model_class | 0.917 | 0.500 | 0.454 | 0.792–1.000 | YES | local-gpu |

Confusion matrix (model_class): `[[12, 0], [2, 10]]`

| batch_size | 0.667 | 0.250 | 0.362 | 0.458–0.833 | YES | local-gpu |

Confusion matrix (batch_size): `[[12, 0, 0, 0], [2, 0, 2, 0], [2, 0, 4, 0], [0, 0, 2, 0]]`

| seq_length | 0.750 | 0.250 | 0.687 | 0.583–0.917 | YES | local-gpu |

Confusion matrix (seq_length): `[[2, 0, 0, 2], [0, 10, 0, 0], [0, 2, 0, 2], [0, 0, 0, 6]]`

| llm_phase | 1.000 | 0.333 | 0.868 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (llm_phase): `[[4, 0, 0], [0, 16, 0], [0, 0, 4]]`



## 3. Upper bound — (a) vm_ground_truth (NOT headline)

### Random forest on in-VM superset (reference only)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS (lo>chance) | Backend |
|------|-----|--------|-----|------------|------------------|---------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (mode): `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.693 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (model_class): `[[12, 0], [0, 12]]`

| batch_size | 1.000 | 0.250 | 1.199 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (batch_size): `[[12, 0, 0, 0], [0, 4, 0, 0], [0, 0, 6, 0], [0, 0, 0, 2]]`

| seq_length | 1.000 | 0.250 | 1.309 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (seq_length): `[[4, 0, 0, 0], [0, 10, 0, 0], [0, 0, 4, 0], [0, 0, 0, 6]]`

| llm_phase | 1.000 | 0.333 | 0.868 | 1.000–1.000 | YES | local-gpu |

Confusion matrix (llm_phase): `[[4, 0, 0], [0, 16, 0], [0, 0, 4]]`



## 4. Honest nulls (binding #3)

Axes where **lower CI ≤ chance** are **negative results** — reported above with confusion matrices, not dropped.

## 5. `simulate` backend (binding #2)

`simulate` is used **only** for `smoke-simulate` and unit tests. **No number in this report** came from `simulate`.

## 6. Train/test hygiene

Holdout by **seed** (entire runs), not random windows within a run. See `pipeline/eval/splits.py`.

## 7. Delta vs arXiv:2507.02770

| They showed | We measure (headline **b**) |
|-------------|----------------------------|
| Size/activity timing leakage exists | Multi-axis **workload inference** accuracy/MI above chance |
| No fine-grained ML labels | Corpus with mode, model class, batch, seq, prefill/decode |

---

**STOP — Phase 1 gate complete.** Await human approval before Phase 2.
