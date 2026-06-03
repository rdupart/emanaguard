# PHASE 3 Report — Mitigation (D3, local only)

**Methodology:** `phase3.0`  
**Backend:** `local-gpu`  
**Gate:** STOP — Phase 3 gate (mitigation measured)

> Phase 3 **approved** for local mitigation work. **Azure Phase 4** and **external claims** remain gated
> (see `docs/EXTERNAL_AZURE_CONDITIONS.md`).

## Mitigation vs leakage (mode, batch_size)

| Mitigation | Axis | Baseline Bal.Acc | Mitigated Bal.Acc | Δ leakage | Bytes overhead |
|------------|------|------------------|-------------------|-----------|----------------|
| size_padding | mode | 1.000 | 0.994 | 0.006 | 0.00x |
| size_padding | batch_size | 0.250 | 0.250 | 0.000 | 0.00x |
| constant_rpc | mode | 1.000 | 1.000 | 0.000 | 0.00x |
| constant_rpc | batch_size | 0.250 | 0.031 | 0.219 | 0.00x |


## Overhead

```json
{
  "size_padding": {
    "bytes_ratio": 0.001087015603173814,
    "event_count_ratio": 1.0
  },
  "constant_rpc": {
    "bytes_ratio": 6.793847519836338e-05,
    "event_count_ratio": 1.0
  }
}
```

## Interpretation

- **size_padding** — hides size classes (4096 B blocks); expect large bytes overhead.
- **constant_rpc** — fixed RPC cadence; expect timing structure collapse.
- Positive **leakage_reduction_balanced** = mitigated observer harder to infer axis.

---

**STOP — Phase 3 gate.** No Azure.
