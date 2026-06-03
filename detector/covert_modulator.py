"""
Tier-Red style covert timing/size modulation on host-observer events.

Implemented for D2 hard-case evaluation only. Algorithm details are research-private;
this module applies a deterministic transform for measurement, not an attack tool.
"""

from __future__ import annotations

import copy

import numpy as np


def apply_covert_modulator(
    host_events: list[dict],
    rng: np.random.Generator,
    *,
    cadence_ns: int = 350_000,
    jitter_fraction: float = 0.25,
) -> list[dict]:
    """
    Perturb inter-transfer cadence and quantize sizes while preserving approximate
    total byte volume (hard violation for policy detector).
    """
    if not host_events:
        return []
    events = copy.deepcopy(sorted(host_events, key=lambda e: e["t_ns"]))
    total_bytes = sum(int(e["size_bytes"]) for e in events)
    out: list[dict] = []
    t = int(events[0]["t_ns"])
    for i, e in enumerate(events):
        t += int(cadence_ns * (1 + rng.uniform(-jitter_fraction, jitter_fraction)))
        sz = max(256, int(e["size_bytes"]))
        out.append(
            {
                "t_ns": t,
                "size_bytes": sz,
                "direction": e["direction"],
                "duration_ns": int(e.get("duration_ns") or cadence_ns // 2),
            }
        )
    # Renormalize total volume roughly preserved
    cur = sum(e["size_bytes"] for e in out) or 1
    scale = total_bytes / cur
    for e in out:
        e["size_bytes"] = max(256, int(e["size_bytes"] * scale))
    return out
