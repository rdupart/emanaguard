"""Generate PHASE_1_REPORT.md from phase1_results.json (Phase 1.3 + labeling gates)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PRELIMINARY_BANNER = """
> **PRELIMINARY** — Do not use in external writeups, applications, or Azure until gates in
> `docs/PRELIMINARY_CAVEATS.md` are satisfied (≥8 architectures, single-draw, held-out-model,
> hard-case detector). Phase 3 **not approved**.
"""


def _fmt_axis_table(results: list[dict], title: str) -> str:
    lines = [
        f"### {title}",
        "",
        "| Axis | Acc | Chance | MI | CI (lo–hi) | PASS | Claim |",
        "|------|-----|--------|-----|------------|------|-------|",
    ]
    for r in results:
        claim = r.get("claim_status", "PRELIMINARY")
        lines.append(
            f"| {r['label_axis']} | {r['accuracy']:.3f} | {r['chance_accuracy']:.3f} | "
            f"{r['mi_bits']:.3f} | {r['ci_lower']:.3f}–{r['ci_upper']:.3f} | "
            f"{'YES' if r['pass_lower_ci_above_chance'] else 'NO'} | {claim} |"
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


def _fmt_labeling_audit(audit: dict) -> str:
    if not audit:
        return "_No labeling audit in JSON — re-run evaluate._\n"
    return f"""
| Field | Value |
|-------|--------|
| Physical distinct `architecture_id` | **{audit.get('physical_distinct_architecture_ids', '?')}** |
| Min for fingerprint claim | {audit.get('min_architectures_for_fingerprint', 8)} |
| `model_class` | **{audit.get('model_class', {}).get('status', 'RETRACTED')}** — do not cite in headline |
| `architecture_id` | **{audit.get('architecture_id', {}).get('status', '?')}** |

{audit.get('explanation', '')}

See `{audit.get('doc', 'docs/architecture_labeling_audit.md')}`.
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
        held_tbl += (
            f"\n**{axis}** — held out `{held.get('held_out_architectures', [])}`; "
            f"train archs `{held.get('train_architectures', [])}`; "
            f"acc={res.get('accuracy', 0):.3f}, PASS={res.get('pass_lower_ci_above_chance')}; "
            f"{res.get('notes', '')}\n"
        )

    gates = data.get("gate_summary", {})
    gate_lines = "\n".join(f"- **{k}:** {v}" for k, v in gates.items()) if gates else ""

    md = f"""# PHASE 1 Report — Workload Inference (Gate v1.3)

**Date:** 2026-06-03  
**Backend:** `{data.get('backend')}`  
**Methodology:** `{data.get('methodology_version', 'phase1.3')}`  
**External claims:** {data.get('external_claims_status', 'BLOCKED')}

{PRELIMINARY_BANNER}

## Gate summary

{gate_lines or '- Re-run evaluate after expanded corpus collect.'}

## 0. Corpus (physical vs observation draws)

{_fmt_corpus(data.get('corpus_statistics', {}))}

## 0b. architecture_id vs model_class (labeling audit)

{_fmt_labeling_audit(data.get('architecture_labeling_audit', {}))}

## 1. Observer aggregation (requirement #1)

| Report key | Interpretation |
|------------|----------------|
| `host_observer_realistic_single_draw` | **REALISTIC** — {single_label} |
| `host_observer_realistic_mean_draw` | **GENEROUS upper bound** — {mean_label} |

### REALISTIC — single draw (headline for non-retracted axes)

{_fmt_axis_table(data.get('host_observer_realistic_single_draw', []), 'Single-draw realistic observer')}

### GENEROUS — mean of 40 draws (upper bound)

{_fmt_axis_table(data.get('host_observer_realistic_mean_draw', data.get('host_observer_realistic', [])), 'Mean-draw realistic observer')}

## 2. Held-out-model validation (requirement #2)

**Gate status:** {held.get('gate_status', 'n/a')}  
**Physical architectures in corpus:** {held.get('distinct_architectures_in_physical_corpus', '?')}  
Split: {held.get('split', '')}  
Aggregation: `{held.get('aggregation', 'single_draw')}`  
{held_tbl}

Do **not** claim model fingerprinting unless `architecture_id` held-out-model passes with ≥8 physical architectures.

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

**STOP — Phase 1 gate (v1.3).** Re-collect on **10-architecture** corpus, then re-run evaluate + detect. Phase 3 blocked.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report/phase1_results.json", root / "PHASE_1_REPORT.md")
