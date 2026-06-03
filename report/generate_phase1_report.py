"""Generate PHASE_1_REPORT.md from phase1_results.json (Phase 1.2 methodology)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


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
            lines.append(f"\n*{r['label_axis']} notes:* {r['notes']}")
        cm = r.get("confusion")
        if cm:
            lines.append(f"\nConfusion (`{r['label_axis']}`): `{cm}`\n")
    return "\n".join(lines) + "\n"


def _fmt_learning_curves(curves: list[dict], axis: str) -> str:
    pts = [c for c in curves if c["label_axis"] == axis]
    if not pts:
        return ""
    lines = [f"#### Learning curve: `{axis}`", "", "| Train base runs | Train samples | Acc | CI lo–hi |", "|-----------------|---------------|-----|----------|"]
    for p in sorted(pts, key=lambda x: x["n_train_base_runs"]):
        lines.append(
            f"| {p['n_train_base_runs']} | {p['n_train_samples']} | {p['accuracy']:.3f} | "
            f"{p['ci_lower']:.3f}–{p['ci_upper']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def _fmt_corpus_stats(stats: dict, obs_per_base: int) -> str:
    rpc = stats.get("runs_per_config", {})
    rows = "\n".join(f"| `{k}` | {v} |" for k, v in sorted(rpc.items()))
    return f"""
| Metric | Value |
|--------|-------|
| **Total evaluation runs** | **{stats.get('total_runs', 0)}** |
| Unique base `local-gpu` captures | {stats.get('unique_base_captures', 0)} |
| Workload configs | {stats.get('num_configs', 0)} |
| Stochastic observations per base capture | {obs_per_base} |
| Mean runs per config | {stats.get('mean_runs_per_config', 0):.1f} |

**Runs per config:**

| config_id | runs |
|-----------|------|
{rows}
"""


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        out_path.write_text(
            "# PHASE 1 Report\n\n**BLOCKED** — missing `report/phase1_results.json`.\n"
        )
        return

    data = json.loads(results_path.read_text())
    if data.get("backend", "").startswith("simulate"):
        print("Refusing simulate backend for gate report.", file=sys.stderr)
        sys.exit(2)

    stats = data.get("corpus_statistics", {})
    obs = data.get("observations_per_base_capture", 40)
    ablation = data.get("ablation_interpretation", {})
    ablation_text = "\n".join(f"- **{k}:** {v}" for k, v in ablation.items()) or "- (no axis flagged as volume-dominated)"

    curves_md = ""
    for axis in ["mode", "model_class", "batch_size", "seq_length", "llm_phase"]:
        curves_md += _fmt_learning_curves(data.get("learning_curves", []), axis)

    md = f"""# PHASE 1 Report — Workload Inference (Gate, v1.2)

**Date:** 2026-06-03  
**Status:** Re-run after methodology fix (realistic observer + scaled corpus)  
**Backend:** `{data.get('backend', 'local-gpu')}`  
**Headline signal set:** `{data.get('headline_signal_set', 'host_observer_realistic')}`

## 0. Corpus scale (requirement #1)

{_fmt_corpus_stats(stats, obs)}

Base captures are from **`local-gpu`** (Colab). Additional runs are **stochastic host-observation replicas** per base capture (jitter, quantization, aggregation) — not new GPU executions. Re-collect with `--repetitions-per-config` for more physical repetitions across time.

Collection-time **background GPU load + jitter** is implemented in `pipeline/workloads/noise.py` for future collects.

## 1. Realistic host observer (requirement #2) — HEADLINE

Transforms in `{data.get('observer_transform_doc', 'pipeline/features/realistic_observer.py')}`:

| Transform | Rationale |
|-----------|-----------|
| Size quantization / 4KiB alignment | Host sees staging-buffer transfer classes, not tensor exact bytes (2507.02770 §CPU–GSP path) |
| 8–256 B RPC buckets | Small-transfer RPC overhead band (2507.02770) |
| Timing jitter | Host clock / scheduling noise |
| Window aggregation (~25 ms) | RPC/command queue batching |

**Not headline:** `host_observer_idealized` (exact byte counts) — upper-bound only.

{_fmt_axis_table(data.get('host_observer_realistic', []), 'Headline: realistic observer (logistic regression)')}

## 2. Ablation — total bytes only (requirement #3)

{_fmt_axis_table(data.get('ablation_volume_only', []), 'Ablation: H2D/D2H/total bytes + count only')}

**Interpretation:**

{ablation_text}

## 3. Idealized vs realistic (sanity)

{_fmt_axis_table(data.get('host_observer_idealized', []), 'Idealized observer (NOT headline — shows label leakage ceiling)')}

## 4. Learning curves (requirement #4)

Holdout: **25% of config_id** groups (entire configs). Classifier uses **one row per base capture** (mean of 40 stochastic observer draws). Curves vary **# training configs**.

{curves_md}

## 5. D3 mitigation preview (requirement #5)

Observer-feature shims (2507.02770-style defenses evaluated at feature layer):

{_fmt_axis_table(data.get('mitigation_preview_d3', {}).get('mitigation_size_padding', []), 'After fixed 4KiB size padding')}

{_fmt_axis_table(data.get('mitigation_preview_d3', {}).get('mitigation_constant_rpc', []), 'After constant-RPC cadence + 256B size')}

**Mitigation readout:** Fixed-size padding removes **batch_size** signal (null) but **train vs infer (mode)** and coarse **llm_phase** volume often **persist** — inference is dominated by aggregate transfer volume, not fine timing. **constant-RPC** disrupts **model_class** more than **mode**. Full driver-level mitigations (Phase 3) still required.

## 6. In-VM upper bound (a) — not headline

{_fmt_axis_table(data.get('vm_ground_truth', []), 'vm_ground_truth (random forest)')}

## 7. Proxy disclaimer

**(b)** metrics are from **non-CC `local-gpu`** — proxy until Phase 4 Azure CC. Do not conflate **(a)** and **(b)**.

## 8. Split policy

{data.get('split_policy', '')}

---

**STOP — Phase 1 gate (v1.2).** Await human approval. **Do not proceed to Phase 2** until approved.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase1_results.json", root / "PHASE_1_REPORT.md")
