# PHASE 1 Report — Workload Inference (Gate, v1.2)

**Date:** 2026-06-03  
**Status:** Re-run after methodology fix (realistic observer + scaled corpus)  
**Backend:** `local-gpu`  
**Headline signal set:** `host_observer_realistic`

## 0. Corpus scale (requirement #1)


| Metric | Value |
|--------|-------|
| **Total evaluation runs** | **34920** |
| Unique base `local-gpu` captures | 873 |
| Workload configs | 12 |
| Stochastic observations per base capture | 40 |
| Mean runs per config | 2910.0 |

**Runs per config:**

| config_id | runs |
|-----------|------|
| `w00_train` | 3120 |
| `w01_train` | 3120 |
| `w02_train_large_n_a` | 3120 |
| `w03_train_large_n_a` | 3120 |
| `w04_infer` | 3120 |
| `w05_infer` | 3000 |
| `w06_infer_large_n_a` | 2720 |
| `w07_infer_large_n_a` | 2720 |
| `w08_infer` | 2720 |
| `w09_infer` | 2720 |
| `w10_infer_large_prefill` | 2720 |
| `w11_infer_large_decode` | 2720 |


Base captures are from **`local-gpu`** (Colab). Additional runs are **stochastic host-observation replicas** per base capture (jitter, quantization, aggregation) — not new GPU executions. Re-collect with `--repetitions-per-config` for more physical repetitions across time.

Collection-time **background GPU load + jitter** is implemented in `pipeline/workloads/noise.py` for future collects.

## 1. Realistic host observer (requirement #2) — HEADLINE

Transforms in `pipeline/features/realistic_observer.py`:

| Transform | Rationale |
|-----------|-----------|
| Size quantization / 4KiB alignment | Host sees staging-buffer transfer classes, not tensor exact bytes (2507.02770 §CPU–GSP path) |
| 8–256 B RPC buckets | Small-transfer RPC overhead band (2507.02770) |
| Timing jitter | Host clock / scheduling noise |
| Window aggregation (~25 ms) | RPC/command queue batching |

**Not headline:** `host_observer_idealized` (exact byte counts) — upper-bound only.

### Headline: realistic observer (logistic regression)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`mode`): `[[136, 0], [2, 76]]`

| model_class | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`model_class`): `[[136, 0], [2, 76]]`

| batch_size | 0.047 | 0.333 | 0.665 | 0.019–0.075 | NO |

Confusion (`batch_size`): `[[10, 0, 58], [0, 0, 68], [2, 0, 0]]`

| seq_length | 0.575 | 0.333 | 0.701 | 0.509–0.636 | YES |

Confusion (`seq_length`): `[[76, 0, 0], [0, 47, 0], [0, 68, 0]]`

| llm_phase | 0.355 | 1.000 | 0.000 | 0.290–0.421 | NO |

Confusion (`llm_phase`): `[[76]]`



## 2. Ablation — total bytes only (requirement #3)

### Ablation: H2D/D2H/total bytes + count only

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.656 | 1.000–1.000 | YES |

Confusion (`mode`): `[[136, 0], [0, 78]]`

| model_class | 1.000 | 0.500 | 0.656 | 1.000–1.000 | YES |

Confusion (`model_class`): `[[136, 0], [0, 78]]`

| batch_size | 0.318 | 0.333 | 0.656 | 0.257–0.383 | NO |

Confusion (`batch_size`): `[[68, 0, 0], [68, 0, 0], [0, 0, 0]]`

| seq_length | 0.364 | 0.333 | 0.656 | 0.299–0.430 | NO |

Confusion (`seq_length`): `[[78, 0, 0], [0, 0, 0], [0, 0, 0]]`

| llm_phase | 0.000 | 1.000 | 0.000 | 0.000–0.000 | NO |

Confusion (`llm_phase`): `[[0]]`



**Interpretation:**

- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 3. Idealized vs realistic (sanity)

### Idealized observer (NOT headline — shows label leakage ceiling)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`mode`): `[[136, 0], [2, 76]]`

| model_class | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`model_class`): `[[136, 0], [2, 76]]`

| batch_size | 0.000 | 0.333 | 0.656 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 68], [0, 0, 68], [2, 0, 0]]`

| seq_length | 0.668 | 0.333 | 0.650 | 0.607–0.724 | YES |

Confusion (`seq_length`): `[[76, 0, 0], [0, 67, 0], [0, 68, 0]]`

| llm_phase | 0.944 | 1.000 | 0.000 | 0.911–0.972 | NO |

Confusion (`llm_phase`): `[[202]]`



## 4. Learning curves (requirement #4)

Holdout: **25% of config_id** groups (entire configs). Classifier uses **one row per base capture** (mean of 40 stochastic observer draws). Curves vary **# training configs**.

#### Learning curve: `mode`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 292 | 1.000 | 1.000–1.000 |
| 5 | 360 | 0.991 | 0.977–1.000 |
| 6 | 428 | 0.958 | 0.930–0.981 |
| 8 | 581 | 0.991 | 0.977–1.000 |
| 9 | 659 | 0.991 | 0.977–1.000 |
#### Learning curve: `model_class`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 292 | 0.991 | 0.977–1.000 |
| 5 | 360 | 0.991 | 0.977–1.000 |
| 6 | 435 | 0.991 | 0.977–1.000 |
| 8 | 581 | 0.991 | 0.977–1.000 |
| 9 | 659 | 0.991 | 0.977–1.000 |
#### Learning curve: `batch_size`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 279 | 0.416 | 0.350–0.481 |
| 5 | 347 | 0.355 | 0.290–0.421 |
| 6 | 425 | 0.355 | 0.290–0.421 |
| 8 | 581 | 0.000 | 0.000–0.000 |
| 9 | 659 | 0.047 | 0.019–0.075 |
#### Learning curve: `seq_length`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 299 | 0.355 | 0.290–0.421 |
| 5 | 367 | 0.355 | 0.290–0.421 |
| 6 | 435 | 0.355 | 0.290–0.421 |
| 8 | 591 | 0.355 | 0.290–0.421 |
| 9 | 659 | 0.575 | 0.509–0.636 |


## 5. D3 mitigation preview (requirement #5)

Observer-feature shims (2507.02770-style defenses evaluated at feature layer):

### After fixed 4KiB size padding

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`mode`): `[[136, 0], [2, 76]]`

| model_class | 0.458 | 0.500 | 0.026 | 0.393–0.528 | NO |

Confusion (`model_class`): `[[22, 114], [2, 76]]`

| batch_size | 0.000 | 0.333 | 0.656 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 68], [0, 0, 68], [2, 0, 0]]`

| seq_length | 0.355 | 0.333 | 0.127 | 0.290–0.421 | NO |

Confusion (`seq_length`): `[[76, 0, 0], [68, 0, 0], [48, 20, 0]]`

| llm_phase | 0.958 | 1.000 | 0.000 | 0.925–0.981 | NO |

Confusion (`llm_phase`): `[[205]]`



### After constant-RPC cadence + 256B size

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.991 | 0.500 | 0.607 | 0.977–1.000 | YES |

Confusion (`mode`): `[[136, 0], [2, 76]]`

| model_class | 0.379 | 0.500 | 0.000 | 0.313–0.444 | NO |

Confusion (`model_class`): `[[5, 131], [2, 76]]`

| batch_size | 0.000 | 0.333 | 0.656 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 68], [0, 0, 68], [2, 0, 0]]`

| seq_length | 0.355 | 0.333 | 0.496 | 0.290–0.421 | NO |

Confusion (`seq_length`): `[[76, 0, 0], [0, 0, 31], [48, 0, 0]]`

| llm_phase | 0.967 | 1.000 | 0.000 | 0.939–0.986 | NO |

Confusion (`llm_phase`): `[[207]]`



**Mitigation readout:** Fixed-size padding removes **batch_size** signal (null) but **train vs infer (mode)** and coarse **llm_phase** volume often **persist** — inference is dominated by aggregate transfer volume, not fine timing. **constant-RPC** disrupts **model_class** more than **mode**. Full driver-level mitigations (Phase 3) still required.

## 6. In-VM upper bound (a) — not headline

### vm_ground_truth (random forest)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.656 | 1.000–1.000 | YES |

Confusion (`mode`): `[[136, 0], [0, 78]]`

| model_class | 1.000 | 0.500 | 0.656 | 1.000–1.000 | YES |

Confusion (`model_class`): `[[136, 0], [0, 78]]`

| batch_size | 0.000 | 0.333 | 0.656 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 68], [0, 0, 68], [0, 0, 0]]`

| seq_length | 0.364 | 0.333 | 0.625 | 0.299–0.430 | NO |

Confusion (`seq_length`): `[[78, 0, 0], [68, 0, 0], [0, 68, 0]]`

| llm_phase | 1.000 | 1.000 | 0.000 | 1.000–1.000 | NO |

Confusion (`llm_phase`): `[[214]]`



## 7. Proxy disclaimer

**(b)** metrics are from **non-CC `local-gpu`** — proxy until Phase 4 Azure CC. Do not conflate **(a)** and **(b)**.

## 8. Split policy

hold out 25% of config_id groups; ML uses one mean feature vector per base capture (40 obs averaged)

---

**STOP — Phase 1 gate (v1.2).** Await human approval. **Do not proceed to Phase 2** until approved.
