"""Generate PHASE_3_REPORT.md from phase3_results.json."""

from __future__ import annotations

import json
from pathlib import Path


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text("# PHASE 3 Report\n\n**BLOCKED** — run `python3 -m pipeline.cli phase3`\n")
        return

    d = json.loads(results_path.read_text())
    rows = ""
    for r in d.get("results", []):
        rows += (
            f"| {r['mitigation']} | {r['label_axis']} | {r['baseline_balanced_accuracy']:.3f} | "
            f"{r['mitigated_balanced_accuracy']:.3f} | {r['leakage_reduction_balanced']:.3f} | "
            f"{r['overhead_bytes_ratio']:.2f}x |\n"
        )

    md = f"""# PHASE 3 Report — Mitigation (D3, local only)

**Methodology:** `{d.get('methodology_version', 'phase3.0')}`  
**Backend:** `{d.get('backend')}`  
**Gate:** {d.get('gate_status', 'STOP')}

> Phase 3 **approved** for local mitigation work. **Azure Phase 4** and **external claims** remain gated
> (see `docs/EXTERNAL_AZURE_CONDITIONS.md`).

## Mitigation vs leakage (mode, batch_size)

| Mitigation | Axis | Baseline Bal.Acc | Mitigated Bal.Acc | Δ leakage | Bytes overhead |
|------------|------|------------------|-------------------|-----------|----------------|
{rows or '| — | — | — | — | — | — |'}

## Overhead

```json
{json.dumps(d.get('overhead', {}), indent=2)}
```

## Interpretation

- **size_padding** — hides size classes (4096 B blocks); expect large bytes overhead.
- **constant_rpc** — fixed RPC cadence; expect timing structure collapse.
- Positive **leakage_reduction_balanced** = mitigated observer harder to infer axis.

---

**STOP — Phase 3 gate.** No Azure.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase3_results.json", root / "PHASE_3_REPORT.md")
