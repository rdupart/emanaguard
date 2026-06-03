"""
Tier-Red style covert timing/size modulation on host-observer events.

Measurement-only transforms for D2 evaluation — not an attack tool.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ModulationStrength:
    name: str
    cadence_ns: int
    jitter_fraction: float
    description: str


MODULATION_PRESETS: dict[str, ModulationStrength] = {
    "light": ModulationStrength(
        name="light",
        cadence_ns=80_000,
        jitter_fraction=0.08,
        description="Low cadence shift (~8% jitter) — subtle timing perturbation",
    ),
    "medium": ModulationStrength(
        name="medium",
        cadence_ns=200_000,
        jitter_fraction=0.15,
        description="Moderate cadence replacement",
    ),
    "heavy": ModulationStrength(
        name="heavy",
        cadence_ns=350_000,
        jitter_fraction=0.25,
        description="Strong cadence quantization (legacy default) — easy to detect",
    ),
}


def apply_covert_modulator(
    host_events: list[dict],
    rng: np.random.Generator,
    *,
    cadence_ns: int = 350_000,
    jitter_fraction: float = 0.25,
    strength: str | None = "heavy",
) -> list[dict]:
    """Perturb cadence/sizes while preserving approximate total byte volume."""
    if strength and strength in MODULATION_PRESETS:
        p = MODULATION_PRESETS[strength]
        cadence_ns = p.cadence_ns
        jitter_fraction = p.jitter_fraction
    if not host_events:
        return []
    events = copy.deepcopy(sorted(host_events, key=lambda e: e["t_ns"]))
    total_bytes = sum(int(e["size_bytes"]) for e in events)
    out: list[dict] = []
    t = int(events[0]["t_ns"])
    for e in events:
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
    cur = sum(e["size_bytes"] for e in out) or 1
    scale = total_bytes / cur
    for e in out:
        e["size_bytes"] = max(256, int(e["size_bytes"] * scale))
    return out


def apply_adaptive_covert_modulator(
    host_events: list[dict],
    rng: np.random.Generator,
    target_feature_vector: np.ndarray,
    feature_fn,
    *,
    max_strength_order: tuple[str, ...] = ("light", "medium", "heavy"),
) -> tuple[list[dict], dict]:
    """
    Choose the weakest preset that still changes the host feature vector vs benign,
    minimizing L2 distance to benign (adaptive adversary vs detector).
    """
    best_events = apply_covert_modulator(host_events, rng, strength="light")
    best_dist = float(np.linalg.norm(feature_fn(best_events) - target_feature_vector))
    chosen = "light"
    for name in max_strength_order:
        cand = apply_covert_modulator(host_events, rng, strength=name)
        dist = float(np.linalg.norm(feature_fn(cand) - target_feature_vector))
        changed = dist > 1e-6
        if changed and dist < best_dist:
            best_dist = dist
            best_events = cand
            chosen = name
        elif changed:
            best_events = cand
            best_dist = dist
            chosen = name
    meta = {
        "chosen_strength": chosen,
        "l2_distance_to_benign_features": best_dist,
        "adaptive_goal": "minimize signature subject to feature change",
    }
    return best_events, meta
