# Gate status — Phase 1.4 / Phase 2.1 (June 2026)

**Branch:** `cursor/phase-2-detector-c1b3`  
**Phase 3 / Azure:** **NOT approved**

## Reading order

1. **`docs/GATE_STATUS.md`** (this file)  
2. **`PHASE_1_REPORT.md`** — v1.4 metrics (majority baseline, balanced accuracy, MI)  
3. **`PHASE_2_REPORT.md`** — detector v2.1 + covert strength sweep  
4. **`docs/detector_inference_inconsistency.md`** — why binary AUC ≠ 12-way inference  
5. **`docs/architecture_labeling_audit.md`**  
6. **`docs/PRELIMINARY_CAVEATS.md`**

## Metric policy (v1.4)

| Item | Policy |
|------|--------|
| Baseline | **Majority class** on train (not 1/n_classes) |
| PASS | Balanced-accuracy CI lower **>** majority **AND** MI ≥ 0.15 bits |
| Subsample | Equal configs per label value before split |
| NULL axes | `seq_length`, `llm_phase` |
| PRELIMINARY_REAL | `mode`, `batch_size` when PASS |

## Phase 1 headline (single-draw, balanced eval)

| Axis | Bal.Acc | Claim | Notes |
|------|---------|-------|-------|
| mode | ~1.0 | PRELIMINARY_REAL | Volume/mode channel |
| batch_size | ~0.5 | PRELIMINARY_REAL | Beats majority under balance |
| architecture_id | ~0.13 | **NEGATIVE** | Held-out **0.0** — no fingerprinting |
| model_class | — | RETRACTED | Confounded |
| seq_length | ~0.25 | **NULL** | Does not beat majority / low MI |
| llm_phase | — | **NULL** | High bal acc but MI fails gate |

## Held-out-model

**architecture_id balanced accuracy = 0.0** → honest bounding result stands.

## Phase 2 detector (v2.1)

| Suite | Headline? | Notes |
|-------|-----------|-------|
| hard_unauthorized_architecture | Yes | AUC ~0.99 — **PARTIAL confound**: at matched (bs, seq), **total_bytes still differs by architecture** (compute volume) |
| hard_covert_modulator_adaptive | Yes | Adaptive adversary; report alongside **light/heavy** |
| hard_covert_modulator_heavy | No | AUC=1.0 not a strong claim alone |
| trivial_mode_change | No | Not a result |

See `detector_inference_audit` in `report/phase2_results.json`.

## Corpus

- **4576** traces in repo  
- Eval uses **balanced config subsample** on existing traces  
- Corpus spec updated for **future** balanced collects (70 configs)

## Phase 3

Blocked pending your review of v1.4 gates.
