# Google Colab — runbook

Colab must use the **repository root** as the working directory and on `PYTHONPATH`. Otherwise:

`ModuleNotFoundError: No module named 'pipeline'`

## One-time setup (run first)

```python
# GPU runtime: Runtime → Change runtime type → GPU

!rm -rf /content/emanaguard
!git clone -b cursor/phase-1-pipeline-c1b3 https://github.com/rdupart/emanaguard.git /content/emanaguard

%cd /content/emanaguard

import sys
sys.path.insert(0, "/content/emanaguard")  # required for `python -m pipeline.cli`

!pip install -q -r requirements.txt

import torch
print("CUDA:", torch.cuda.is_available())
!nvidia-smi
```

## Collect traces (GPU)

```python
%cd /content/emanaguard
import os
os.environ["PYTHONPATH"] = "/content/emanaguard"

!python3 -m pipeline.cli collect \
  --backend local-gpu \
  --out-dir data/traces \
  --seeds 0,1,2,3,4,5,6,7 \
  --repetitions-per-config 1
```

## Evaluate + report (CPU or GPU)

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

## Download results

```python
from google.colab import files
files.download("/content/emanaguard/report/phase1_results.json")
files.download("/content/emanaguard/PHASE_1_REPORT.md")
```

## Alternative (one line per command)

Prefix every shell command with `PYTHONPATH=/content/emanaguard`:

```python
!cd /content/emanaguard && PYTHONPATH=. python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces --observations-per-base 40 --out-json report/phase1_results.json
```
