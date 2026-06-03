"""
D3 preview: obfuscations applied to realistic host-observer event streams (trace-level).

Not driver shims — measures whether inference survives defenses a lab might deploy.
"""

from __future__ import annotations

import copy

from pipeline.features.realistic_observer import STAGING_BLOCK_BYTES


def mitigate_size_padding(host_events: list[dict]) -> list[dict]:
    """Pad every observed transfer to a fixed staging block (hides size classes)."""
    out = copy.deepcopy(host_events)
    for e in out:
        e["size_bytes"] = STAGING_BLOCK_BYTES
    return out


def mitigate_constant_rpc(host_events: list[dict]) -> list[dict]:
    """
    Constant-time RPC style: collapse to fixed small RPC size and regular cadence.
    Inspired by 2507.02770 recommendation (evaluated here at observer feature layer).
    """
    if not host_events:
        return []
    t0 = host_events[0]["t_ns"]
    interval_ns = 500_000  # 0.5 ms synthetic RPC tick
    out: list[dict] = []
    for i, e in enumerate(host_events):
        out.append(
            {
                "t_ns": t0 + i * interval_ns,
                "size_bytes": 256,
                "direction": e["direction"],
                "duration_ns": e.get("duration_ns"),
            }
        )
    return out
