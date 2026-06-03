# PHASE 1 Report — Workload Inference (Gate, v1.2)

**Date:** 2026-06-03  
**Status:** Re-run after methodology fix (realistic observer + scaled corpus)  
**Backend:** `local-gpu`  
**Headline signal set:** `host_observer_realistic`

## 0. Corpus scale (requirement #1)


| Metric | Value |
|--------|-------|
| **Total evaluation runs** | **3840** |
| Unique base `local-gpu` captures | 96 |
| Workload configs | 12 |
| Stochastic observations per base capture | 40 |
| Mean runs per config | 320.0 |

**Runs per config:**

| config_id | runs |
|-----------|------|
| `w00_train` | 320 |
| `w01_train` | 320 |
| `w02_train_large_n_a` | 320 |
| `w03_train_large_n_a` | 320 |
| `w04_infer` | 320 |
| `w05_infer` | 320 |
| `w06_infer_large_n_a` | 320 |
| `w07_infer_large_n_a` | 320 |
| `w08_infer` | 320 |
| `w09_infer` | 320 |
| `w10_infer_large_prefill` | 320 |
| `w11_infer_large_decode` | 320 |


Base captures are from **`local-gpu`** (Colab). Additional runs are **stochastic host-observation replicas** per base capture (jitter, quantization, aggregation) — not new GPU executions. Re-collect with `--repetitions-per-config` for more physical repetitions across time.

Collection-time **background GPU load + jitter** is implemented in `pipeline/workloads/noise.py` for future collects.

## 1. Realistic host observer (requirement #2) — HEADLINE

Transforms in `pipeline/features/realistic_observer.py`:

| Transform | Rationale |
|-----------|-----------|
| Size quantization / 4KiB alignment | Host sees staging-buffer transfer classes, not tensor exact bytes (2507.02770 §CPU–GSP path) |
| 8–256 B RPC buckets | Small-transfer RPC overhead band (2507.02770) |
| Timing jitter | Host clock / scheduling noise |
| Window aggregation (~8 ms) | RPC/command queue batching |

**Not headline:** `host_observer_idealized` (exact byte counts) — upper-bound only.

### Headline: realistic observer (logistic regression)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`mode`): `[[16, 0], [1, 7]]`

| model_class | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`model_class`): `[[16, 0], [1, 7]]`

| batch_size | 0.333 | 0.333 | 0.968 | 0.167–0.542 | NO |

Confusion (`batch_size`): `[[8, 0, 0], [0, 0, 8], [1, 0, 0]]`

| seq_length | 0.292 | 0.333 | 0.968 | 0.125–0.500 | NO |

Confusion (`seq_length`): `[[7, 0, 0], [0, 0, 0], [0, 8, 0]]`

| llm_phase | 0.292 | 1.000 | 0.000 | 0.125–0.500 | NO |

Confusion (`llm_phase`): `[[7]]`



## 2. Ablation — total bytes only (requirement #3)

### Ablation: H2D/D2H/total bytes + count only

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion (`mode`): `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion (`model_class`): `[[16, 0], [0, 8]]`

| batch_size | 0.333 | 0.333 | 0.637 | 0.167–0.542 | NO |

Confusion (`batch_size`): `[[8, 0, 0], [8, 0, 0], [0, 0, 0]]`

| seq_length | 0.333 | 0.333 | 0.637 | 0.125–0.542 | NO |

Confusion (`seq_length`): `[[8, 0, 0], [0, 0, 0], [0, 0, 0]]`

| llm_phase | 0.333 | 1.000 | 0.000 | 0.125–0.542 | NO |

Confusion (`llm_phase`): `[[8]]`



**Interpretation:**

- **mode:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.
- **model_class:** Coarse volume leakage: total-bytes ablation within 5% of full realistic features.

## 3. Idealized vs realistic (sanity)

### Idealized observer (NOT headline — shows label leakage ceiling)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`mode`): `[[16, 0], [1, 7]]`

| model_class | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`model_class`): `[[16, 0], [1, 7]]`

| batch_size | 0.000 | 0.333 | 0.637 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 8], [0, 0, 8], [1, 0, 0]]`

| seq_length | 0.292 | 0.333 | 0.968 | 0.125–0.500 | NO |

Confusion (`seq_length`): `[[7, 0, 0], [0, 0, 0], [0, 8, 0]]`

| llm_phase | 0.958 | 1.000 | 0.000 | 0.875–1.000 | NO |

Confusion (`llm_phase`): `[[23]]`



## 4. Learning curves (requirement #4)

Holdout: **25% of config_id** groups (entire configs). Classifier uses **one row per base capture** (mean of 40 stochastic observer draws). Curves vary **# training configs**.

#### Learning curve: `mode`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 2 | 16 | 1.000 | 1.000–1.000 |
| 2 | 16 | 1.000 | 1.000–1.000 |
| 4 | 32 | 0.417 | 0.208–0.625 |
| 5 | 40 | 0.333 | 0.125–0.542 |
| 6 | 48 | 1.000 | 1.000–1.000 |
| 8 | 64 | 0.958 | 0.875–1.000 |
| 9 | 72 | 0.958 | 0.875–1.000 |
#### Learning curve: `model_class`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 32 | 0.958 | 0.875–1.000 |
| 5 | 40 | 0.958 | 0.875–1.000 |
| 6 | 48 | 0.958 | 0.875–1.000 |
| 8 | 64 | 0.958 | 0.875–1.000 |
| 9 | 72 | 0.958 | 0.875–1.000 |
#### Learning curve: `batch_size`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 4 | 32 | 0.625 | 0.417–0.833 |
| 5 | 40 | 0.625 | 0.417–0.833 |
| 6 | 48 | 0.625 | 0.417–0.833 |
| 8 | 64 | 0.333 | 0.167–0.542 |
| 9 | 72 | 0.333 | 0.167–0.542 |
#### Learning curve: `seq_length`

| Train base runs | Train samples | Acc | CI lo–hi |
|-----------------|---------------|-----|----------|
| 2 | 16 | 0.292 | 0.125–0.500 |
| 2 | 16 | 0.292 | 0.125–0.500 |
| 4 | 32 | 0.000 | 0.000–0.000 |
| 5 | 40 | 0.292 | 0.125–0.500 |
| 6 | 48 | 0.292 | 0.125–0.500 |
| 8 | 64 | 0.292 | 0.125–0.500 |
| 9 | 72 | 0.292 | 0.125–0.500 |


## 5. D3 mitigation preview (requirement #5)

Observer-feature shims (2507.02770-style defenses evaluated at feature layer):

### After fixed 4KiB size padding

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`mode`): `[[16, 0], [1, 7]]`

| model_class | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`model_class`): `[[16, 0], [1, 7]]`

| batch_size | 0.000 | 0.333 | 0.637 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 8], [0, 0, 8], [1, 0, 0]]`

| seq_length | 0.292 | 0.333 | 0.048 | 0.125–0.500 | NO |

Confusion (`seq_length`): `[[7, 0, 0], [8, 0, 0], [8, 0, 0]]`

| llm_phase | 0.958 | 1.000 | 0.000 | 0.875–1.000 | NO |

Confusion (`llm_phase`): `[[23]]`



### After constant-RPC cadence + 256B size

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 0.958 | 0.500 | 0.478 | 0.875–1.000 | YES |

Confusion (`mode`): `[[16, 0], [1, 7]]`

| model_class | 0.292 | 0.500 | 0.048 | 0.125–0.500 | NO |

Confusion (`model_class`): `[[0, 16], [1, 7]]`

| batch_size | 0.000 | 0.333 | 0.637 | 0.000–0.000 | NO |

Confusion (`batch_size`): `[[0, 0, 8], [0, 0, 8], [1, 0, 0]]`

| seq_length | 0.292 | 0.333 | 0.667 | 0.125–0.500 | NO |

Confusion (`seq_length`): `[[7, 0, 0], [0, 0, 8], [8, 0, 0]]`

| llm_phase | 0.958 | 1.000 | 0.000 | 0.875–1.000 | NO |

Confusion (`llm_phase`): `[[23]]`



**Mitigation readout:** Fixed-size padding removes **batch_size** signal (null) but **train vs infer (mode)** and coarse **llm_phase** volume often **persist** — inference is dominated by aggregate transfer volume, not fine timing. **constant-RPC** disrupts **model_class** more than **mode**. Full driver-level mitigations (Phase 3) still required.

## 6. In-VM upper bound (a) — not headline

### vm_ground_truth (random forest)

| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |
|------|-----|--------|-----|------------|------|
| mode | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion (`mode`): `[[16, 0], [0, 8]]`

| model_class | 1.000 | 0.500 | 0.637 | 1.000–1.000 | YES |

Confusion (`model_class`): `[[16, 0], [0, 8]]`

| batch_size | 0.333 | 0.333 | 1.099 | 0.167–0.542 | NO |

Confusion (`batch_size`): `[[8, 0, 0], [0, 0, 8], [0, 0, 0]]`

| seq_length | 0.417 | 0.333 | 0.492 | 0.208–0.625 | NO |

Confusion (`seq_length`): `[[8, 0, 0], [6, 2, 0], [0, 8, 0]]`

| llm_phase | 1.000 | 1.000 | 0.000 | 1.000–1.000 | NO |

Confusion (`llm_phase`): `[[24]]`



## 7. Proxy disclaimer

**(b)** metrics are from **non-CC `local-gpu`** — proxy until Phase 4 Azure CC. Do not conflate **(a)** and **(b)**.

## 8. Split policy

hold out 25% of config_id groups; ML uses one mean feature vector per base capture (40 obs averaged)

---

**STOP — Phase 1 gate (v1.2).** Await human approval. **Do not proceed to Phase 2** until approved.
