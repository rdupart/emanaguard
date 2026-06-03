# Push Colab traces from Downloads to cursor/phase-2-detector-c1b3
# Usage (PowerShell):
#   .\scripts\push_traces_windows.ps1
#   .\scripts\push_traces_windows.ps1 -TracesDir "C:\Users\rsocc\Downloads\traces"

param(
    [string]$TracesDir = "C:\Users\rsocc\Downloads\traces",
    [string]$CloneDir = "$env:USERPROFILE\emanaguard-traces",
    [string]$Branch = "cursor/phase-2-detector-c1b3"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $TracesDir)) {
    Write-Error "Traces folder not found: $TracesDir"
}

if (-not (Test-Path $CloneDir)) {
    git clone -b $Branch "https://github.com/rdupart/emanaguard.git" $CloneDir
}
Set-Location $CloneDir
git fetch origin
git checkout $Branch
git pull origin $Branch

$dest = Join-Path $CloneDir "data\traces"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item (Join-Path $TracesDir "*.jsonl") -Destination $dest -Force
Copy-Item (Join-Path $TracesDir "manifest*.json") -Destination $dest -Force

$count = (Get-ChildItem $dest -Filter *.jsonl).Count
Write-Host "Copied $count jsonl files to data/traces"

git add data/traces/
git status
git commit -m "data: add Colab local-gpu trace corpus ($count jsonl files)"
git push -u origin $Branch
Write-Host "Done. Verify on GitHub: branch $Branch, folder data/traces"
