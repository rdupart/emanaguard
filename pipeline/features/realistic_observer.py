"""
Realistic malicious-host observer model (headline signal set b).

Models what a host watching ENCRYPTED CPU↔GSP staging traffic plausibly infers,
without exact per-copy plaintext sizes or in-VM CUDA metadata.

Mechanism basis (not rediscovering the channel):
- arXiv:2507.02770 — staging buffers in unprotected memory; host sees transfer
  timing and size classes; small (8–256 B) RPC-dominated vs ~4 KiB payload path.
- NVIDIA HCC whitepaper / CC blog — encrypted payloads; metadata timing/volume.

Transforms (label-blind, applied per observation sample):
1. Size quantization + alignment padding to staging/RPC buckets.
2. Timing jitter on observed timestamps and durations (host clock noise).
3. Window aggregation batching (multiple logical copies collapse per interval).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pipeline.features.host_observer import host_observer_feature_vector
from pipeline.trace.events import Direction

# 2507.02770: 8B–256B RPC overhead band; ~4KiB large-transfer regime
RPC_BUCKET_MAX = 256
STAGING_BLOCK_BYTES = 4096


def quantize_observed_size(size_bytes: int, rng: np.random.Generator) -> int:
    """Round up to defensible staging/RPC buckets; host does not see exact tensor bytes."""
    if size_bytes <= 8:
        base = 8
    elif size_bytes <= RPC_BUCKET_MAX:
        base = int(2 ** np.ceil(np.log2(max(size_bytes, 8))))
        base = min(base, RPC_BUCKET_MAX)
    else:
        base = int(
            np.ceil(size_bytes / STAGING_BLOCK_BYTES) * STAGING_BLOCK_BYTES
        )
    # Occasional extra padding byte (encryption alignment uncertainty)
    if rng.random() < 0.15:
        base += int(rng.choice([8, 16, 256]))
    return base


def apply_realistic_observer(
    host_events: list[dict],
    rng: np.random.Generator,
    *,
    jitter_us_mean: float = 120.0,
    jitter_us_sigma: float = 80.0,
    aggregate_window_ns: int = 25_000_000,
    drop_fraction: float = 0.08,
) -> list[dict]:
    """
    Stochastic host-side view of one run. Same logical workload can yield different
  observations under jitter/aggregation (used for scaled repetitions).
    """
    if not host_events:
        return []

    observed: list[dict] = []
    for e in host_events:
        if rng.random() < drop_fraction:
            continue
        jitter_ns = int(rng.normal(jitter_us_mean * 1e3, jitter_us_sigma * 1e3))
        t_ns = int(e["t_ns"]) + jitter_ns
        qsize = quantize_observed_size(int(e["size_bytes"]), rng)
        dur = e.get("duration_ns") or 0
        dur_j = max(
            0,
            int(dur + rng.normal(jitter_us_mean * 1e3, jitter_us_sigma * 1e3)),
        )
        observed.append(
            {
                "t_ns": t_ns,
                "size_bytes": qsize,
                "direction": e["direction"],
                "duration_ns": dur_j,
            }
        )

    observed.sort(key=lambda x: x["t_ns"])
    return _aggregate_windows(observed, aggregate_window_ns)


def _aggregate_windows(events: list[dict], window_ns: int) -> list[dict]:
    """Batch transfers in a host sampling window (RPC/command queue coalescing)."""
    if not events:
        return []
    batches: list[dict] = []
    cur_dir = events[0]["direction"]
    t0 = events[0]["t_ns"]
    total_size = 0
    total_dur = 0
    count = 0

    for e in events:
        if e["t_ns"] - t0 > window_ns and count > 0:
            batches.append(
                {
                    "t_ns": t0,
                    "size_bytes": quantize_observed_size(
                        total_size, np.random.default_rng(t0 & 0xFFFF)
                    ),
                    "direction": cur_dir,
                    "duration_ns": total_dur // max(count, 1),
                }
            )
            t0 = e["t_ns"]
            cur_dir = e["direction"]
            total_size = 0
            total_dur = 0
            count = 0
        if e["direction"] != cur_dir and count > 0:
            batches.append(
                {
                    "t_ns": t0,
                    "size_bytes": total_size,
                    "direction": cur_dir,
                    "duration_ns": total_dur // max(count, 1),
                }
            )
            t0 = e["t_ns"]
            cur_dir = e["direction"]
            total_size = 0
            total_dur = 0
            count = 0
        total_size += int(e["size_bytes"])
        total_dur += int(e.get("duration_ns") or 0)
        count += 1

    if count > 0:
        batches.append(
            {
                "t_ns": t0,
                "size_bytes": total_size,
                "direction": cur_dir,
                "duration_ns": total_dur // max(count, 1),
            }
        )
    return batches


def realistic_observer_features(
    host_events: list[dict], rng: np.random.Generator | None = None
) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    observed = apply_realistic_observer(host_events, rng)
    return host_observer_feature_vector(observed)


def volume_only_features(host_events: list[dict], rng: np.random.Generator) -> np.ndarray:
    """Ablation: total bytes + event count only (coarse volume channel)."""
    observed = apply_realistic_observer(host_events, rng)
    if not observed:
        return np.zeros(4, dtype=np.float64)
    sizes = np.array([e["size_bytes"] for e in observed], dtype=np.float64)
    dirs = np.array([e["direction"] for e in observed])
    h2d = float(np.sum(sizes[dirs == Direction.H2D.value]))
    d2h = float(np.sum(sizes[dirs == Direction.D2H.value]))
    return np.array([h2d, d2h, h2d + d2h, float(len(observed))], dtype=np.float64)
