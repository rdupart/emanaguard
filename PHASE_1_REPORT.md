# PHASE 1 Report — Workload Inference (Gate)

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
