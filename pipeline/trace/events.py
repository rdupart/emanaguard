"""Transfer event schema — ground-truth capture vs host-observer projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Direction(str, Enum):
    H2D = "H2D"
    D2H = "D2H"


@dataclass(frozen=True)
class TransferEvent:
    """Single staging-buffer–equivalent transfer episode (in-VM capture)."""

    t_ns: int
    size_bytes: int
    direction: Direction
    duration_ns: int | None = None
    # --- in-VM ground truth only (stripped for host-observer) ---
    op_name: str | None = None
    stream_id: int | None = None
    phase: str | None = None
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["direction"] = self.direction.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransferEvent:
        return cls(
            t_ns=int(data["t_ns"]),
            size_bytes=int(data["size_bytes"]),
            direction=Direction(data["direction"]),
            duration_ns=data.get("duration_ns"),
            op_name=data.get("op_name"),
            stream_id=data.get("stream_id"),
            phase=data.get("phase"),
            run_id=data.get("run_id"),
        )


@dataclass
class RunLabels:
    """Multi-axis labels for one workload run (used for evaluation only)."""

    workload_id: str
    mode: str  # train | infer
    model_class: str  # small | large
    batch_size: int
    seq_length: int
    llm_phase: str  # prefill | decode | n/a
    seed: int
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunLabels:
        return cls(**data)
