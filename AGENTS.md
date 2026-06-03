## Cursor Cloud specific instructions

### Product

Python research pipeline for **host-observer (b)** workload inference at the H100 CC boundary. No web app, no Azure in Phase 1.

### Dependencies (update script handles this)

```bash
pip install -r requirements.txt
```

CPU PyTorch is enough for **evaluate** on committed traces in `data/traces/`. **collect** requires CUDA (`local-gpu`).

### Common commands

| Task | Command |
|------|---------|
| Evaluate traces | `python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces` |
| Regenerate gate report | `python3 report/generate_phase1_report.py` |
| Tests (no GPU) | `python3 -m pytest tests/ -q` |
| Plumbing only | `python3 -m pipeline.cli smoke-simulate` |

### Gotchas

- Traces live in **`data/traces/`** (96 `*.jsonl` runs + manifests), not `data/traces/local-gpu/`.
- `evaluate` **rejects** `--backend simulate` for publication metrics.
- `load_trace_dir` skips non-`*.jsonl` files (manifests are `.json`).
- This VM often has **no GPU**; use committed traces + evaluate rather than collect.
