# Gate status — Phase 3 approved (local)

**Branch:** `cursor/phase-2-detector-c1b3`  
**Phase 3:** **APPROVED** (mitigation/D3, local only)  
**Azure / external:** **GATED** — see `docs/EXTERNAL_AZURE_CONDITIONS.md`

## Reading order

1. **`docs/GATE_STATUS.md`** (this file)  
2. **`PHASE_3_REPORT.md`** — mitigation leakage vs overhead  
3. **`PHASE_2_REPORT.md`** — detector v2.2 (volume-level, bytes-matched, covert capacity)  
4. **`PHASE_1_REPORT.md`** — inference v1.4  
5. **`docs/EXTERNAL_AZURE_CONDITIONS.md`**  
6. **`docs/detector_inference_inconsistency.md`**

## llm_phase NULL (correct rationale)

**NOT** because metrics fail majority (balanced acc can be **1.0**, MI **> 0.15**).

**NULL because:**
- **Volume-confounded** — total-bytes ablation ≈ full realistic observer (~1.0 acc)
- **Minority-class fragility** — balanced eval with small per-class support on prefill/decode

## Phase 2 detector honesty

| Suite | Role |
|-------|------|
| `hard_unauthorized_architecture_volume_level` | Reframed volume-level violation at matched (bs, seq); report **bal vs majority margin** (weak if <0.05) |
| `hard_unauthorized_architecture_bytes_matched` | ±5% total_bytes pairs, timing-only features — tests non-volume signal |
| `hard_covert_modulator_adaptive` | Search below 95th-%ile benign threshold; report FPR @ op point |
| `hard_covert_modulator_heavy` | Not headline (AUC=1 not strong) |

## Phase 3 commands

```bash
python3 -m pipeline.cli phase3 --trace-dir data/traces
python3 report/generate_phase3_report.py
```

Full gate refresh (long):

```bash
python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces
python3 -m pipeline.cli detect --trace-dir data/traces
python3 -m pipeline.cli phase3 --trace-dir data/traces
```

## Phase 1 inference (unchanged bounding result)

Held-out **architecture_id** balanced acc **0.0** — no fingerprinting claim.
