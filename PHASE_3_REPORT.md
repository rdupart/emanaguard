# PHASE 3 Report — Mitigation (D3, local only)

**Methodology:** `phase3.1`  
**Backend:** `local-gpu`  
**Phase-1 baseline source:** `report/phase1_results.json`  
**Gate:** STOP — Phase 3 gate (mitigation measured)

> Phase 1 **accepted**. Phase 4 / Azure **GATED** — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.

## Mitigation vs leakage (Phase-1 canonical baseline)

| Mitigation | Axis | P1 baseline Bal.Acc | Mitigated Bal.Acc | Δ vs P1 (reportable?) | Bytes overhead |
|------------|------|----------------------|-------------------|------------------------|----------------|
| size_padding | mode | 1.000 | 1.000 | 0.000 (no) | 1.000x |
| size_padding | batch_size | 0.500 | 0.445 | — (no) | 1.000x |
| constant_rpc | mode | 1.000 | 1.000 | 0.000 (no) | 0.000x |
| constant_rpc | batch_size | 0.500 | 0.250 | — (no) | 0.000x |
| constant_volume | mode | 1.000 | 1.000 | 0.000 (no) | 0.399x |
| constant_volume | batch_size | 0.500 | 0.250 | — (no) | 0.399x |


**Leakage policy:** Reduction only vs Phase-1 canonical baseline when axis_leaks=true; do not claim reduction from null/non-leaking baselines

**Overhead:** post-realistic_observer stream; bytes_ratio=mitigated/baseline (pad-up >=1)

## Volume channel

- **size_padding_on_mode**: No reportable reduction on mode (size/cadence defense; does not remove total-volume channel)
- **constant_rpc_on_mode**: No reportable volume-channel reduction (expected)
- **constant_volume_on_mode**: Phase-1 baseline bal=1.000 → mitigated=1.000; reportable reduction=False

## Overhead (detail)

```json
{
  "size_padding": {
    "bytes_ratio": 1.0003302886495173,
    "event_count_ratio": 1.001489831897301,
    "time_span_ratio": 1.0003234269254786,
    "detail": {
      "mean_baseline_total_bytes": 318450680.21153843,
      "mean_mitigated_total_bytes": 318555860.8566434,
      "mean_baseline_events": 52.80550699300699,
      "mean_mitigated_events": 52.88417832167832,
      "bugfix": "measured post-realistic_observer (was wrongly compared raw host vs mitigated raw)",
      "pad_up_semantics": "size_padding uses max(size, block) so bytes_ratio must be >= 1"
    },
    "bytes_ratio_interpretation": "mitigated/baseline total bytes on observer path; pad-up mitigations expect >= 1"
  },
  "constant_rpc": {
    "bytes_ratio": 4.251317548248438e-05,
    "event_count_ratio": 1.001489831897301,
    "time_span_ratio": 0.034561299209892794,
    "detail": {
      "mean_baseline_total_bytes": 318450680.21153843,
      "mean_mitigated_total_bytes": 13538.34965034965,
      "mean_baseline_events": 52.80550699300699,
      "mean_mitigated_events": 52.88417832167832,
      "bugfix": "measured post-realistic_observer (was wrongly compared raw host vs mitigated raw)",
      "pad_up_semantics": "size_padding uses max(size, block) so bytes_ratio must be >= 1"
    },
    "bytes_ratio_interpretation": "constant_rpc fixes 256 B RPCs \u2014 total bytes may shrink vs baseline"
  },
  "constant_volume": {
    "bytes_ratio": 0.39883609482284377,
    "event_count_ratio": 1.001489831897301,
    "time_span_ratio": 1.0003234269254786,
    "detail": {
      "mean_baseline_total_bytes": 318450680.21153843,
      "mean_mitigated_total_bytes": 127009625.68924825,
      "mean_baseline_events": 52.80550699300699,
      "mean_mitigated_events": 52.88417832167832,
      "bugfix": "measured post-realistic_observer (was wrongly compared raw host vs mitigated raw)",
      "pad_up_semantics": "size_padding uses max(size, block) so bytes_ratio must be >= 1"
    },
    "bytes_ratio_interpretation": "constant_volume targets corpus median (ratio near 1 on average)"
  }
}
```

## Honest findings

- **size_padding / constant_rpc** — shape size or cadence; they do **not** remove total-byte volume leakage on `mode`.
- **constant_volume** — volume-shaping to corpus median total bytes; measure `mode` reduction vs overhead.

---

**STOP — Phase 3 gate.** No Azure.
