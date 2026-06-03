"""Generate PHASE_1_REPORT.md from phase1_results.json (local-gpu only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _fmt_axis_table(results: list[dict], title: str) -> str:
    lines = [f"### {title}", "", "| Axis | Acc | Chance | MI | CI (lo–hi) | PASS (lo>chance) | Backend |", "|------|-----|--------|-----|------------|------------------|---------|"]
    for r in results:
        lines.append(
            f"| {r['label_axis']} | {r['accuracy']:.3f} | {r['chance_accuracy']:.3f} | "
            f"{r['mi_bits']:.3f} | {r['ci_lower']:.3f}–{r['ci_upper']:.3f} | "
            f"{'YES' if r['pass_lower_ci_above_chance'] else 'NO'} | {r['backend']} |"
        )
        if r.get("notes"):
            lines.append(f"\n*Notes ({r['label_axis']}):* {r['notes']}")
        cm = r.get("confusion")
        if cm:
            lines.append(f"\nConfusion matrix ({r['label_axis']}): `{cm}`\n")
    return "\n".join(lines) + "\n"


def generate(results_path: Path, out_path: Path) -> None:
    if not results_path.exists():
        body = """# PHASE 1 Report — Workload Inference (Gate)

**Date:** 2026-06-03  
**Status:** **BLOCKED — no `local-gpu` traces collected in this environment**

## Execution blocker

This Cloud Agent VM has **no CUDA GPU** (`torch.cuda.is_available() == False`). Per Phase 1 binding condition **#2**, **no accuracy/MI/ROC numbers are reported** from `simulate` or synthetic data.

### Required commands (GPU host)

```bash
pip install -r requirements.txt
# Install CUDA-matched PyTorch per https://pytorch.org/get-started/locally/
python -m pipeline.cli collect --backend local-gpu --out-dir data/traces/local-gpu --seeds 0,1,2,3,4,5,6,7
python -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces/local-gpu --out-json report/phase1_results.json
python report/generate_phase1_report.py
```

### Pipeline validation (this VM)

- `python3 -m pytest tests/ -q`: **7 passed** (host-observer projection, metrics CI, simulate plumbing guards)
- `python3 -m pipeline.cli smoke-simulate`: plumbing only — **not cited in metrics**

## Corpus (labeled workloads)

12 workload specs × 8 seeds (default) = 96 runs. Axes: `mode`, `model_class`, `batch_size`, `seq_length`, `llm_phase` (`n/a` | `prefill` | `decode`). See `pipeline/workloads/corpus.py`.

## Classifiers

| Signal set | Model |
|------------|-------|
| (a) vm_ground_truth | Random forest on 48-dim superset |
| (b) host_observer | Logistic regression on 32-dim aggregate features |
| (b) sequence | MLP on 128-step size-bucket sequence |

## Observer validity (binding #1)

| Set | Role | Used for headline? |
|-----|------|-------------------|
| **(a) `vm_ground_truth`** | In-VM CUDA/profiler superset | **No** — upper bound + label alignment only |
| **(b) `host_observer`** | Timing, size, direction, count, cadence only | **Yes** |
| **(b) proxy caveat** | Collected on **non-CC** `local-gpu` | **Proxy/upper-bound** for true malicious-host vantage until **Phase 4 Azure CC** |

## Binding compliance

1. **(a)/(b) reported separately** — implemented in `pipeline/eval/phase1_eval.py`; results pending `local-gpu` JSON.
2. **`simulate` not used for reported metrics** — enforced in CLI (`evaluate` rejects simulate).
3. **Honest nulls** — failed axes retain confusion matrices; PASS = lower bootstrap CI > chance.

## Delta vs arXiv:2507.02770

We **do not** claim discovery of the CPU–GSP timing/size channel. Phase 1 measures **incremental workload semantics** from host-legitimate features (D1).

---

**STOP — Phase 1 gate.** Re-run report generation after `report/phase1_results.json` exists.
"""
        out_path.write_text(body)
        return

    data = json.loads(results_path.read_text())
    backend = data.get("backend", "local-gpu")
    if backend.startswith("simulate"):
        print("Refusing to generate report from simulate backend.", file=sys.stderr)
        sys.exit(2)

    md = f"""# PHASE 1 Report — Workload Inference (Gate)

**Date:** 2026-06-03  
**Backend for all metrics below:** `{backend}`  
**Headline signal set:** **(b) host_observer** (and sequence variant)

## 1. Observer validity (binding #1)

| Set | Definition | Headline? |
|-----|------------|-----------|
| **(a) `vm_ground_truth`** | In-VM features including `op_name`, `phase`, `stream` — see `pipeline/features/vm_ground_truth.py` | **No** — labels + upper bound only |
| **(b) `host_observer`** | Timing, size, direction, count, cadence — see `pipeline/features/host_observer.py` | **Yes** |

**Proxy disclaimer:** All **(b)** numbers below were collected on **`local-gpu` (non-CC)**. This is a **proxy/upper-bound** for the true malicious-host vantage under H100 CC-On. **Phase 4 (`azure-cc`)** must confirm ranking and magnitudes. **Do not conflate (a) and (b).**

## 2. Headline results — (b) host_observer

{_fmt_axis_table(data['host_observer'], 'Tabular (logistic regression on aggregate features)')}

{_fmt_axis_table(data.get('host_observer_sequence', []), 'Sequence model (MLP on size-bucket sequence)')}

## 3. Upper bound — (a) vm_ground_truth (NOT headline)

{_fmt_axis_table(data['vm_ground_truth'], 'Random forest on in-VM superset (reference only)')}

## 4. Honest nulls (binding #3)

Axes where **lower CI ≤ chance** are **negative results** — reported above with confusion matrices, not dropped.

## 5. `simulate` backend (binding #2)

`simulate` is used **only** for `smoke-simulate` and unit tests. **No number in this report** came from `simulate`.

## 6. Train/test hygiene

Holdout by **seed** (entire runs), not random windows within a run. See `pipeline/eval/splits.py`.

## 7. Delta vs arXiv:2507.02770

| They showed | We measure (headline **b**) |
|-------------|----------------------------|
| Size/activity timing leakage exists | Multi-axis **workload inference** accuracy/MI above chance |
| No fine-grained ML labels | Corpus with mode, model class, batch, seq, prefill/decode |

---

**STOP — Phase 1 gate complete.** Await human approval before Phase 2.
"""
    out_path.write_text(md)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "report" / "phase1_results.json", root / "PHASE_1_REPORT.md")
