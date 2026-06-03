"""Signal set (b): host-observer features — GPU-CC threat-model legal only."""

from __future__ import annotations

import numpy as np
from pipeline.trace.events import Direction, TransferEvent

# Allowed: timing, size, direction, count, transfer cadence.
# Forbidden: op_name, stream, phase, kernel/CUDA semantics, plaintext.


def project_host_observer(events: list[TransferEvent]) -> list[dict]:
    """Strip in-VM-only fields; return host-legitimate event records."""
    out: list[dict] = []
    for e in events:
        out.append(
            {
                "t_ns": e.t_ns,
                "size_bytes": e.size_bytes,
                "direction": e.direction.value,
                "duration_ns": e.duration_ns,
            }
        )
    return out


def host_observer_feature_vector(host_events: list[dict]) -> np.ndarray:
    """
    Aggregate window features from host-visible transfer events only.
    No label access; deterministic given events.
    """
    if not host_events:
        return np.zeros(32, dtype=np.float64)

    sizes = np.array([e["size_bytes"] for e in host_events], dtype=np.float64)
    times = np.array([e["t_ns"] for e in host_events], dtype=np.float64)
    durs = np.array(
        [e.get("duration_ns") or 0 for e in host_events], dtype=np.float64
    )
    dirs = np.array([1.0 if e["direction"] == Direction.H2D.value else 0.0 for e in host_events])

    gaps = np.diff(times) if len(times) > 1 else np.array([0.0])
    total_span_s = max((times[-1] - times[0]) / 1e9, 1e-9)

    h2d_mask = dirs > 0.5
    d2h_mask = ~h2d_mask

    buckets = [8, 64, 256, 4096, 65536]
    hist = []
    for lo, hi in zip(buckets[:-1], buckets[1:]):
        hist.append(float(np.sum((sizes >= lo) & (sizes < hi))))
    hist.append(float(np.sum(sizes >= buckets[-1])))

    feats = [
        float(len(host_events)),
        float(np.sum(sizes)),
        float(np.sum(sizes) / total_span_s),
        float(np.mean(sizes)),
        float(np.std(sizes)) if len(sizes) > 1 else 0.0,
        float(np.median(sizes)),
        float(np.min(sizes)),
        float(np.max(sizes)),
        float(np.sum(h2d_mask)),
        float(np.sum(d2h_mask)),
        float(np.sum(sizes[h2d_mask]) if np.any(h2d_mask) else 0.0),
        float(np.sum(sizes[d2h_mask]) if np.any(d2h_mask) else 0.0),
        float(np.mean(gaps) / 1e6) if len(gaps) else 0.0,
        float(np.std(gaps) / 1e6) if len(gaps) > 1 else 0.0,
        float(np.min(gaps) / 1e6) if len(gaps) else 0.0,
        float(np.max(gaps) / 1e6) if len(gaps) else 0.0,
        float(len(host_events) / total_span_s),
        float(np.mean(durs) / 1e6) if len(durs) else 0.0,
        float(np.std(durs) / 1e6) if len(durs) > 1 else 0.0,
        float(np.percentile(sizes, 25)),
        float(np.percentile(sizes, 75)),
        float(np.percentile(sizes, 90)),
        float(np.percentile(gaps, 50) / 1e6) if len(gaps) else 0.0,
        float(np.percentile(gaps, 90) / 1e6) if len(gaps) else 0.0,
        float(np.sum(sizes < 256)),
        float(np.sum(sizes >= 4096)),
        float(np.sum((sizes >= 8) & (sizes < 256)) / max(len(sizes), 1)),
        float(np.sum(sizes >= 4096) / max(len(sizes), 1)),
    ]
    feats.extend(hist)
    vec = np.array(feats, dtype=np.float64)
    if vec.size < 32:
        vec = np.pad(vec, (0, 32 - vec.size))
    return vec[:32]


def host_observer_sequence(host_events: list[dict], max_len: int = 128) -> np.ndarray:
    """Size-bucket sequence for sequence model (host-visible only)."""
    buckets = np.array([8, 64, 256, 1024, 4096, 16384, 65536], dtype=np.float64)

    def bucket_idx(sz: float) -> int:
        for i, b in enumerate(buckets):
            if sz < b:
                return i
        return len(buckets)

    seq = np.zeros(max_len, dtype=np.float64)
    for i, e in enumerate(host_events[:max_len]):
        seq[i] = bucket_idx(float(e["size_bytes"]))
    return seq
