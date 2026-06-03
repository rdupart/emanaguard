"""Signal set (a): in-VM ground-truth features — labels + upper-bound reference only."""

from __future__ import annotations

import numpy as np
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.trace.events import TransferEvent


def vm_ground_truth_feature_vector(events: list[TransferEvent]) -> np.ndarray:
    """
    Superset features available inside the CVM (CUDA/profiler view).
    NOT for headline leakage claims — upper bound / label alignment only.
    """
    host = project_host_observer(events)
    base = host_observer_feature_vector(host)

    if not events:
        extra = np.zeros(16, dtype=np.float64)
        return np.concatenate([base, extra])

    op_hashes = []
    phases = []
    streams = []
    for e in events:
        op_hashes.append(hash(e.op_name or "") % 1000)
        phases.append(hash(e.phase or "") % 100)
        streams.append(float(e.stream_id or 0))

    op_arr = np.array(op_hashes, dtype=np.float64)
    phase_arr = np.array(phases, dtype=np.float64)
    stream_arr = np.array(streams, dtype=np.float64)

    extra = np.array(
        [
            float(len(set(op_hashes))),
            float(np.mean(op_arr)),
            float(np.std(op_arr)) if len(op_arr) > 1 else 0.0,
            float(len(set(phases))),
            float(np.mean(phase_arr)),
            float(np.std(phase_arr)) if len(phase_arr) > 1 else 0.0,
            float(len(set(streams))),
            float(np.mean(stream_arr)),
            float(np.std(stream_arr)) if len(stream_arr) > 1 else 0.0,
            float(sum(1 for e in events if e.op_name and "weight" in e.op_name.lower())),
            float(sum(1 for e in events if e.op_name and "forward" in e.op_name.lower())),
            float(sum(1 for e in events if e.op_name and "backward" in e.op_name.lower())),
            float(sum(1 for e in events if e.phase == "prefill")),
            float(sum(1 for e in events if e.phase == "decode")),
            float(sum(1 for e in events if e.phase == "train_step")),
            float(sum(1 for e in events if e.phase == "infer_step")),
        ],
        dtype=np.float64,
    )
    return np.concatenate([base, extra])
