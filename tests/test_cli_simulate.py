"""Simulate backend plumbing tests only."""

from __future__ import annotations

import subprocess
import sys


def test_smoke_simulate_exits_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "pipeline.cli", "smoke-simulate", "--seeds", "0,1"],
        capture_output=True,
        text=True,
        cwd="/workspace",
    )
    assert proc.returncode == 0, proc.stderr
    assert "simulate-PLUMBING-ONLY" in proc.stdout
    assert "NOT valid" in proc.stderr or "NOT valid" in proc.stdout + proc.stderr


def test_evaluate_rejects_simulate():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pipeline.cli",
            "evaluate",
            "--backend",
            "simulate",
        ],
        capture_output=True,
        text=True,
        cwd="/workspace",
    )
    assert proc.returncode == 2
