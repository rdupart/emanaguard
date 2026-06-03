#!/usr/bin/env bash
# Run on a CUDA-capable host (Colab, RunPod, bare metal). Not for simulate metrics.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m pip install -r requirements.txt
python3 -m pipeline.cli collect --backend local-gpu --out-dir data/traces --seeds "${SEEDS:-0,1,2,3,4,5,6,7}"
python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces --out-json report/phase1_results.json
python3 report/generate_phase1_report.py
echo "Wrote PHASE_1_REPORT.md"
