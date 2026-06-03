# Uploading traces from Windows to GitHub

Your Colab **`report/phase1_results.json`** / **`phase2_results.json`** can be committed from the browser; **trace JSONL files** are too large to pass through the cloud agent. Push them from your PC.

**Target branch:** `cursor/phase-2-detector-c1b3`  
**Local folder:** `C:\Users\rsocc\Downloads\traces` (should contain `*.jsonl` and `manifest*.json`)

## Quick path (script in repo)

```powershell
git clone -b cursor/phase-2-detector-c1b3 https://github.com/rdupart/emanaguard.git
cd emanaguard
.\scripts\push_traces_windows.ps1 -TracesDir "C:\Users\rsocc\Downloads\traces"
```

## Option A — Git Bash or PowerShell (manual)

```powershell
cd C:\Users\rsocc\Downloads\traces

# One-time: clone the repo branch (skip if you already have a clone)
cd $HOME
git clone -b cursor/phase-2-detector-c1b3 https://github.com/rdupart/emanaguard.git emanaguard-traces
cd emanaguard-traces

# Copy traces into the repo (adjust source path if needed)
Copy-Item -Path "C:\Users\rsocc\Downloads\traces\*.jsonl" -Destination "data\traces\" -Force
Copy-Item -Path "C:\Users\rsocc\Downloads\traces\manifest*.json" -Destination "data\traces\" -Force

git add data/traces/*.jsonl data/traces/manifest*.json
git status

# Large push? May take several minutes. If >100MB, consider Git LFS (see below).
git commit -m "data: add Colab local-gpu trace corpus (10-arch collect)"
git push -u origin cursor/phase-2-detector-c1b3
```

## Option B — Zip upload via GitHub web UI

If the folder is **under ~25 MB** per file / **under repo limits**, zip `traces` and attach to a commit on the branch via GitHub Desktop or the website. For **thousands** of JSONL files, Option A is more reliable.

## Git LFS (if push is rejected for size)

```powershell
git lfs install
git lfs track "data/traces/*.jsonl"
git add .gitattributes
git add data/traces/*.jsonl
git commit -m "data: trace corpus via LFS"
git push -u origin cursor/phase-2-detector-c1b3
```

## Verify after push

On any machine with the repo:

```bash
ls data/traces/*.jsonl | wc -l   # expect thousands, not ~96
python3 -m pipeline.cli evaluate --backend local-gpu --trace-dir data/traces --observations-per-base 40
```

Reproduced metrics should match your Colab `report/phase1_results.json` (± small split variance).
