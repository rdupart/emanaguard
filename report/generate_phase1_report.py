"""Generate PHASE_1_REPORT.md from phase1_results.json (Phase 1.3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PRELIMINARY_BANNER = """
> **PRELIMINARY** — Do not use in external writeups, applications, or Azure until gates in
> `docs/PRELIMINARY_CAVEATS.md` are satisfied (single-draw reporting, held-out-model, physical scale).
"""


def _fmt_axis_table(results: list[dict], title: str) -> str:
    lines = [
        f"### {title}",
        "",
        "| Axis | Acc | Chance | MI | CI (lo–hi) | PASS |",
        "|------|-----|--------|-----|------------|------|",
    ]
    for r in results:
        lines.append(
            f"| {r['label_axis']} | {r['accuracy']:.3f} | {r['chance_accuracy']:.3f} | "
            f"{r['mi_bits']:.3f} | {r['ci_lower']:.3f}–{r['ci_upper']:.3f} | "
            f"{'YES' if r['pass_lower_ci_above_chance'] else 'NO'} |"
        )
        if r.get("notes"):
            lines.append(f"\n*{r['label_axis']}:* {r['notes']}")
        if r.get("confusion"):
            lines.append(f"\nConfusion: `{r['confusion']}`\n")
    return "\n".join(lines) + "\n"


def _fmt_corpus(stats: dict) -> str:
    return f"""
| Metric | Value |
|--------|--------|
| **Physical base captures** | **{stats.get('physical_base_captures', stats.get('unique_base_captures', 0))}** |
| Stochastic observation draws | {stats.get('stochastic_observation_draws', stats.get('total_runs', 0))} |
| Workload configs | {stats.get('num_configs', 0)} |

*{stats.get('terminology_note', '')}*
"""


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text("# PHASE 1 Report\n\n**BLOCKED** — missing results JSON.\n")
        return

    data = json.loads(results_path.read_text())
    if data.get("backend", "").startswith("simulate"):
        print("Refusing simulate backend.", file=sys.stderr)
        sys.exit(2)

    labels = data.get("observer_aggregation_labels", {})
    mean_label = labels.get("host_observer_realistic_mean_draw", "mean draw")
    single_label = labels.get("host_observer_realistic_single_draw", "single draw")

    held = data.get("held_out_model_evaluation", {})
    held_tbl = ""
    for axis, res in held.get("axes", {}).items():
        held_tbl += f"\n**{axis}** (held-out architectures `{held.get('held_out_architectures', [])}`): "
        held_tbl += f"acc={res.get('accuracy', 0):.3f}, PASS={res.get('pass_lower_ci_above_chance')}, {res.get('notes', '')}\n"

    md = f"""# PHASE 1 Report — Workload Inference (Gate v1.3)

**Date:** 2026-06-03  
**Backend:** `{data.get('backend')}`  
**Methodology:** `{data.get('methodology_version', 'phase1.3')}`  
**External claims:** {data.get('external_claims_status', 'BLOCKED')}

{PRELIMINARY_BANNER}

## 0. Corpus (physical vs observation draws)

{_fmt_corpus(data.get('corpus_statistics', {}))}

## 1. Observer aggregation (requirement #1)

| Report key | Interpretation |
|------------|----------------|
| `host_observer_realistic_single_draw` | **REALISTIC** — {single_label} |
| `host_observer_realistic_mean_draw` | **GENEROUS upper bound** — {mean_label} |

### REALISTIC — single draw (headline for claims)

{_fmt_axis_table(data.get('host_observer_realistic_single_draw', []), 'Single-draw realistic observer')}

### GENEROUS — mean of 40 draws (upper bound)

{_fmt_axis_table(data.get('host_observer_realistic_mean_draw', data.get('host_observer_realistic', [])), 'Mean-draw realistic observer')}

## 2. Held-out-model validation (requirement #2)

Split: {held.get('split', '')}  
Aggregation: `{held.get('aggregation', 'single_draw')}`  
{held_tbl}

## 3. Ablation (volume only)

{_fmt_axis_table(data.get('ablation_volume_only', []), 'Total bytes ablation')}

{chr(10).join('- **' + k + ':** ' + v for k, v in data.get('ablation_interpretation', {}).items()) or '- (none flagged)'}

## 4. D3 mitigation preview

See `mitigation_preview_d3` in JSON.

## 5. Idealized observer (not headline)

{_fmt_axis_table(data.get('host_observer_idealized', []), 'Idealized')}

## 6. Azure

Not run (Phase 4).

---

**STOP — Phase 1 gate (v1.3).** Phase 2 approved in parallel; detector inherits preliminary caveat.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase1_results.json", root / "PHASE_1_REPORT.md")
