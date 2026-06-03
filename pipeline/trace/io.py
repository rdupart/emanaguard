"""JSONL trace persistence."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.trace.events import RunLabels, TransferEvent


def write_run(
    out_dir: Path,
    events: list[TransferEvent],
    labels: RunLabels,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{labels.run_id}.jsonl"
    with path.open("w") as f:
        f.write(json.dumps({"type": "labels", **labels.to_dict()}) + "\n")
        for e in events:
            f.write(json.dumps({"type": "event", **e.to_dict()}) + "\n")
    return path


def read_run(path: Path) -> tuple[list[TransferEvent], RunLabels]:
    events: list[TransferEvent] = []
    labels: RunLabels | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            if row.get("type") == "labels":
                row.pop("type", None)
                labels = RunLabels.from_dict(row)
            elif row.get("type") == "event":
                row.pop("type", None)
                events.append(TransferEvent.from_dict(row))
    if labels is None:
        raise ValueError(f"No labels in {path}")
    return events, labels


def load_trace_dir(trace_dir: Path) -> list[tuple[list[TransferEvent], RunLabels]]:
    runs = []
    for p in sorted(trace_dir.glob("*.jsonl")):
        runs.append(read_run(p))
    return runs
