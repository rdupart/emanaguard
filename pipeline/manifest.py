"""Deterministic run manifest logging for reproducibility."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunManifest:
    run_id: str
    backend: str
    seed: int
    command: list[str]
    started_at: str
    git_commit: str | None = None
    python_version: str = field(default_factory=lambda: sys.version)
    platform: str = field(default_factory=platform.platform)
    torch_cuda: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")


def git_head() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def make_run_id(backend: str, seed: int, tag: str = "") -> str:
    raw = f"{backend}:{seed}:{tag}:{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def new_manifest(
    backend: str,
    seed: int,
    argv: list[str] | None = None,
    **extra: Any,
) -> RunManifest:
    try:
        import torch

        cuda = bool(torch.cuda.is_available())
    except ImportError:
        cuda = None

    return RunManifest(
        run_id=make_run_id(backend, seed),
        backend=backend,
        seed=seed,
        command=argv or sys.argv,
        started_at=datetime.now(timezone.utc).isoformat(),
        git_commit=git_head(),
        torch_cuda=cuda,
        extra=extra,
    )
