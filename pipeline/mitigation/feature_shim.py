"""
D3: obfuscations on realistic host-observer event streams (post-observer).

Measured on the **same path as classification** (realistic_observer → mitigate → features).
"""

from __future__ import annotations

import copy

import numpy as np

from pipeline.features.realistic_observer import STAGING_BLOCK_BYTES


def mitigate_size_padding_observer(obs_events: list[dict]) -> list[dict]:
    """Pad each observed transfer up to staging block size (never shrink — fixes overhead bug)."""
    out = copy.deepcopy(obs_events)
    for e in out:
        e["size_bytes"] = max(int(e["size_bytes"]), STAGING_BLOCK_BYTES)
    return out


def mitigate_size_padding(host_events: list[dict]) -> list[dict]:
    """Legacy entry: pad raw host events up (prefer observer-path API)."""
    out = copy.deepcopy(host_events)
    for e in out:
        e["size_bytes"] = max(int(e["size_bytes"]), STAGING_BLOCK_BYTES)
    return out


def mitigate_constant_rpc_observer(obs_events: list[dict]) -> list[dict]:
    """Constant cadence + fixed RPC size on observer-visible events."""
    if not obs_events:
        return []
    t0 = obs_events[0]["t_ns"]
    interval_ns = 500_000
    out: list[dict] = []
    for i, e in enumerate(obs_events):
        out.append(
            {
                "t_ns": t0 + i * interval_ns,
                "size_bytes": 256,
                "direction": e["direction"],
                "duration_ns": e.get("duration_ns"),
            }
        )
    return out


def mitigate_constant_rpc(host_events: list[dict]) -> list[dict]:
    return mitigate_constant_rpc_observer(host_events)


def mitigate_constant_volume_observer(
    obs_events: list[dict],
    target_total_bytes: int,
) -> list[dict]:
    """
    Rescale observed transfer sizes so total bytes = target (volume-shaping / constant-volume).

    Targets the total-volume channel that size-padding and constant-RPC do not remove.
    """
    if not obs_events:
        return []
    out = copy.deepcopy(obs_events)
    cur = sum(int(e["size_bytes"]) for e in out) or 1
    target = max(int(target_total_bytes), 1)
    scale = target / cur
    for e in out:
        e["size_bytes"] = max(256, int(e["size_bytes"] * scale))
    return out


def reference_total_bytes_median(
    runs_observer_totals: list[int],
) -> int:
    """Corpus reference total bytes (median observer-visible total per capture)."""
    if not runs_observer_totals:
        return STAGING_BLOCK_BYTES * 32
    return int(np.median(runs_observer_totals))
