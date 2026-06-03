# emanaguard — Host-Observable I/O Metadata at the H100 CC Boundary

Defensive research: **workload inference (D1)** and **policy-deviation detection (D2)** from **host-legitimate** staging-buffer transfer metadata under the GPU Confidential Computing threat model. Extends [arXiv:2507.02770](https://arxiv.org/abs/2507.02770); does **not** claim rediscovery of the CPU–GSP timing/size channel.

**Status:** Phase 1 pipeline (see `PHASE_1_REPORT.md`).

## Requirements

- Python 3.10+
- **Phase 1 metrics:** CUDA GPU + PyTorch with CUDA (`local-gpu` backend)
- **Plumbing/tests:** CPU only (`simulate` via `smoke-simulate`)

```bash
pip install -r requirements.txt
# On GPU host, install CUDA-matched PyTorch: https://pytorch.org/get-started/locally/
```

## Phase 1 commands

```bash
# Collect real traces (requires CUDA)
python3 -m pipeline.cli collect --backend local-gpu \
  --out-dir data/traces/local-gpu --seeds 0,1,2,3,4,5,6,7

# Evaluate — headline metrics from host_observer (b) only
python3 -m pipeline.cli evaluate --backend local-gpu \
  --trace-dir data/traces/local-gpu --out-json report/phase1_results.json

# Regenerate gate report
python3 report/generate_phase1_report.py

# Plumbing smoke (NOT for publication numbers)
python3 -m pipeline.cli smoke-simulate --seeds 0,1

# Unit tests
python3 -m pytest tests/ -q
```

## Repository layout

| Path | Purpose |
|------|---------|
| `pipeline/` | Trace collection, (a)/(b) features, evaluation |
| `detector/` | Phase 2 (stub) |
| `mitigation/` | Phase 3 (stub) |
| `report/` | Results JSON + report generator |
| `docs/` | D4 overlay placeholder |
| `data/traces/` | Collected `local-gpu` JSONL traces |

## Signal sets (Phase 1 binding)

| Set | Module | Role |
|-----|--------|------|
| **(a)** `vm_ground_truth` | `pipeline/features/vm_ground_truth.py` | In-VM upper bound — **not** headline |
| **(b)** `host_observer` | `pipeline/features/host_observer.py` | **Headline** — proxy on non-CC until Phase 4 |

## Literature & gates

- `related_work.md`, `delta_assessment.md`, `observer_feasibility.md`, `cc_tenancy.md`
- `PHASE_0_REPORT.md`, `PHASE_0.5_REPORT.md`, `PHASE_1_REPORT.md`
- `DISCLOSURE.md`

## Azure

**Phase 4 only** — `azure-cc` backend is not implemented in Phase 1.
