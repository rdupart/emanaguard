"""Generate PHASE_3_REPORT.md from phase3_results.json (D3 v3.1)."""

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
        red = r.get("leakage_reduction_vs_phase1_baseline")
        red_s = f"{red:.3f}" if red is not None else "—"
        rep = "yes" if r.get("leakage_reduction_reportable") else "no"
        rows += (
            f"| {r['mitigation']} | {r['label_axis']} | "
            f"{r.get('phase1_canonical_baseline_balanced_accuracy', 0):.3f} | "
            f"{r.get('mitigated_balanced_accuracy', 0):.3f} | {red_s} ({rep}) | "
            f"{r.get('overhead_bytes_ratio', 1):.3f}x |\n"
        )

    vol = d.get("volume_channel_findings", {})
    vol_txt = "\n".join(f"- **{k}**: {v}" for k, v in vol.items())

    md = f"""# PHASE 3 Report — Mitigation (D3, local only)

**Methodology:** `{d.get('methodology_version', 'phase3.1')}`  
**Backend:** `{d.get('backend')}`  
**Phase-1 baseline source:** `{d.get('phase1_baseline_source', 'report/phase1_results.json')}`  
**Gate:** {d.get('gate_status', 'STOP')}

> Phase 1 **accepted**. Phase 4 / Azure **GATED** — see `docs/EXTERNAL_AZURE_CONDITIONS.md`.

## Mitigation vs leakage (Phase-1 canonical baseline)

| Mitigation | Axis | P1 baseline Bal.Acc | Mitigated Bal.Acc | Δ vs P1 (reportable?) | Bytes overhead |
|------------|------|----------------------|-------------------|------------------------|----------------|
{rows or '| — | — | — | — | — | — |'}

**Leakage policy:** {d.get('leakage_policy', '')}

**Overhead:** {d.get('overhead_measurement', '')}

## Volume channel

{vol_txt or '_No volume findings._'}

## Overhead (detail)

```json
{json.dumps(d.get('overhead', {}), indent=2)}
```

## Honest findings

- **size_padding / constant_rpc** — shape size or cadence; they do **not** remove total-byte volume leakage on `mode`.
- **constant_volume** — volume-shaping to corpus median total bytes; measure `mode` reduction vs overhead.

---

**STOP — Phase 3 gate.** No Azure.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase3_results.json", root / "PHASE_3_REPORT.md")
