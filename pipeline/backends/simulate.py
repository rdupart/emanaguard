"""
Simulate backend — pipeline plumbing and unit tests ONLY.

MUST NOT be used to produce reported accuracy/MI/ROC (Phase 1 binding).
Synthetic events are NOT derived from labels.
"""

from __future__ import annotations

import random

from pipeline.trace.events import Direction, RunLabels, TransferEvent
from pipeline.workloads.corpus import WorkloadSpec


def synthetic_events_for_test(
    n_events: int = 40,
    seed: int = 0,
) -> list[TransferEvent]:
    """Label-independent synthetic transfer stream for plumbing tests."""
    rng = random.Random(seed)
    events: list[TransferEvent] = []
    t = 0
    for _ in range(n_events):
        size = rng.choice([64, 128, 256, 4096, 16384])
        direction = Direction.H2D if rng.random() > 0.4 else Direction.D2H
        dur = rng.randint(1000, 500000)
        events.append(
            TransferEvent(
                t_ns=t,
                size_bytes=size,
                direction=direction,
                duration_ns=dur,
                op_name="synthetic_test",
                stream_id=0,
                phase="test",
                run_id="simulate_test",
            )
        )
        t += rng.randint(100_000, 5_000_000)
    return events


def simulate_run(
    spec: WorkloadSpec,
    seed: int,
    run_id: str,
) -> tuple[list[TransferEvent], RunLabels]:
    """
    Produce a fixed plumbing trace (not for publication metrics).
    Event statistics depend only on seed + workload_id string hash, not label fields.
    """
    rng = random.Random(seed ^ hash(spec.workload_id))
    n_events = 20 + (hash(spec.workload_id) % 30)
    events: list[TransferEvent] = []
    t = 0
    for i in range(n_events):
        size = rng.choice([8, 64, 256, 4096, 8192])
        direction = Direction.H2D if i % 3 != 2 else Direction.D2H
        events.append(
            TransferEvent(
                t_ns=t,
                size_bytes=size,
                direction=direction,
                duration_ns=rng.randint(500, 200000),
                op_name="simulate_plumbing",
                stream_id=i % 2,
                phase="plumbing",
                run_id=run_id,
            )
        )
        t += rng.randint(50_000, 2_000_000)

    labels = RunLabels(
        workload_id=spec.workload_id,
        mode=spec.mode,
        model_class=spec.model_class,
        batch_size=spec.batch_size,
        seq_length=spec.seq_length,
        llm_phase=spec.llm_phase,
        seed=seed,
        run_id=run_id,
        architecture_id=spec.architecture_id,
    )
    return events, labels
