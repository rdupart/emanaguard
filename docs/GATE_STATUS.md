# Gate status — Phase 1 accepted; Phase 4 / Azure GATED

**Branch:** `cursor/phase-2-detector-c1b3`  
**Phase 1:** **ACCEPTED** (inference v1.4)  
**Phase 2:** **v2.3** — bytes-matched UNTESTABLE when n_pairs=0; covert **amplitude sweep** (no “≈zero capacity” preset claim)  
**Phase 3:** **v3.1** — observer-path overhead; Phase-1 canonical baselines; **constant_volume** volume-shaping  
**Azure / external:** **GATED** — see `docs/EXTERNAL_AZURE_CONDITIONS.md`

## Reading order

1. **`docs/GATE_STATUS.md`** (this file)  
2. **`PHASE_3_REPORT.md`** — mitigation leakage vs overhead (Phase-1-aligned)  
3. **`PHASE_2_REPORT.md`** — detector v2.3  
4. **`PHASE_1_REPORT.md`** — inference v1.4  
5. **`docs/EXTERNAL_AZURE_CONDITIONS.md`**  
6. **`docs/detector_inference_inconsistency.md`**

## llm_phase NULL (correct rationale)

**NOT** because metrics fail majority (balanced acc can be **1.0**, MI **> 0.15**).

**NULL because:**
- **Volume-confounded** — total-bytes ablation ≈ full realistic observer (~1.0 acc)
- **Minority-class fragility** — balanced eval with small per-class support on prefill/decode

## Phase 2 detector honesty (v2.3)

| Suite | Role |
|-------|------|
| `hard_unauthorized_architecture_volume_level` | Volume-level violation at matched (bs, seq); **bal vs majority margin** |
| `hard_unauthorized_architecture_bytes_matched` | **UNTESTABLE_OPEN_QUESTION** if n_pairs=0 at ±10% — not a resolved negative |
| `hard_covert_modulator_adaptive` | Continuous cadence-amplitude sweep; capacity claim only from sweep curve |
| `hard_covert_modulator_heavy` / `light` | Presets detectable; not headline capacity claims |

## Phase 3 mitigation honesty (v3.1)

| Mitigation | Volume channel |
|------------|----------------|
| `size_padding` | Does **not** reportably reduce `mode` leakage (pad-up overhead bytes_ratio ≥ 1) |
| `constant_rpc` | Does **not** target total volume; batch_size claims vs **Phase-1 bal=0.5** only |
| `constant_volume` | Shapes total bytes to corpus median; report **mode** reduction vs bytes overhead |

Overhead measured **post-realistic_observer** (fixes raw-host vs observer-path bug).

## Commands

```bash
python3 -m pipeline.cli detect --trace-dir data/traces
python3 -m pipeline.cli phase3 --trace-dir data/traces
python3 report/generate_phase2_report.py
python3 report/generate_phase3_report.py
```

Full refresh:

```bash
python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces
python3 -m pipeline.cli detect --trace-dir data/traces
python3 -m pipeline.cli phase3 --trace-dir data/traces
```

## Phase 1 inference (bounding result)

Held-out **architecture_id** balanced acc **0.0** — no fingerprinting claim.
