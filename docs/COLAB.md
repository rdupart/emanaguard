# Google Colab — runbook

Colab must use the **repository root** as the working directory and on `PYTHONPATH`. Otherwise:

`ModuleNotFoundError: No module named 'pipeline'`

**Branch for gates:** `cursor/phase-2-detector-c1b3` (Phase 1 + Phase 2; not Phase 3).

## One-time setup (run first)

```python
# GPU runtime: Runtime → Change runtime type → GPU

!rm -rf /content/emanaguard
!git clone -b cursor/phase-2-detector-c1b3 https://github.com/rdupart/emanaguard.git /content/emanaguard

%cd /content/emanaguard

import os
import sys
sys.path.insert(0, "/content/emanaguard")
os.environ["PYTHONPATH"] = "/content/emanaguard"

!pip install -q -r requirements.txt

import torch
print("CUDA:", torch.cuda.is_available())
!nvidia-smi
```

## Collect traces (GPU) — 10-arch corpus

```python
%cd /content/emanaguard
import os
os.environ["PYTHONPATH"] = "/content/emanaguard"

!python3 -m pipeline.cli collect \
  --backend local-gpu \
  --out-dir data/traces \
  --seeds 0,1,2,3,4,5,6,7 \
  --repetitions-per-config 20
```

## Phase 1 evaluate + report

```python
%cd /content/emanaguard
import os
os.environ["PYTHONPATH"] = "/content/emanaguard"

!python3 -m pipeline.cli evaluate \
  --backend local-gpu \
  --trace-dir data/traces \
  --observations-per-base 40 \
  --out-json report/phase1_results.json

!python3 report/generate_phase1_report.py
```

## Phase 2 detect + report

```python
%cd /content/emanaguard
import os
os.environ["PYTHONPATH"] = "/content/emanaguard"

!python3 -m pipeline.cli detect \
  --backend local-gpu \
  --trace-dir data/traces \
  --out-json report/phase2_results.json

!python3 report/generate_phase2_report.py
```

## Download results

```python
from google.colab import files
for p in [
    "report/phase1_results.json",
    "report/phase2_results.json",
    "PHASE_1_REPORT.md",
    "PHASE_2_REPORT.md",
]:
    files.download(f"/content/emanaguard/{p}")
```

**Traces:** Zip `data/traces` and copy to your PC, then push with **`docs/TRACES_WINDOWS_UPLOAD.md`**. GitHub does not need the JSON if you already uploaded `phase1_results.json` / `phase2_results.json`, but the repo needs traces for independent re-run.

## Alternative (one line per command)

```python
!cd /content/emanaguard && PYTHONPATH=. python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces --observations-per-base 40
```

## After Colab

1. Upload **`report/phase1_results.json`** and **`report/phase2_results.json`** to GitHub (you did this on `main`).
2. Push **`data/traces`** from Windows — see **`docs/TRACES_WINDOWS_UPLOAD.md`**.
3. Read **`docs/GATE_STATUS.md`**, then **`PHASE_1_REPORT.md`** and **`PHASE_2_REPORT.md`**.
