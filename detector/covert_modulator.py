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
        description="Strong cadence quantization — legacy default",
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


def apply_covert_modulator_scaled(
    host_events: list[dict],
    rng: np.random.Generator,
    *,
    cadence_scale: float = 1.0,
    jitter_fraction: float = 0.08,
) -> list[dict]:
    """Fine-grained strength via cadence multiplier (for adaptive search)."""
    base = MODULATION_PRESETS["light"]
    return apply_covert_modulator(
        host_events,
        rng,
        cadence_ns=int(base.cadence_ns * cadence_scale),
        jitter_fraction=jitter_fraction,
        strength=None,
    )


def search_adaptive_covert_below_threshold(
    host_events: list[dict],
    rng: np.random.Generator,
    benign_feature_vector: np.ndarray,
    feature_fn,
    violation_score_fn,
    *,
    threshold: float,
    cadence_scales: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0),
) -> tuple[list[dict], dict]:
    """
  Search for weakest modulation that still changes features but scores below detector threshold.

    Models covert capacity under the detector operating point (bit-encoding style cadence tweaks).
    """
    base_feat = benign_feature_vector
    best_events = host_events
    best_meta: dict = {
        "evades_detector": True,
        "chosen_cadence_scale": 0.0,
        "l2_distance": 0.0,
        "score": 0.0,
        "threshold": threshold,
    }

    # No modulation — should not evade if benign
    score0 = float(violation_score_fn(host_events))
    if score0 < threshold:
        best_meta["warning"] = "benign scores below threshold without modulation"

    found_subtle = False
    for scale in cadence_scales:
        mod = apply_covert_modulator_scaled(host_events, rng, cadence_scale=scale)
        feat = feature_fn(mod)
        dist = float(np.linalg.norm(feat - base_feat))
        if dist < 1e-9:
            continue
        score = float(violation_score_fn(mod))
        if score < threshold:
            best_events = mod
            best_meta = {
                "evades_detector": True,
                "chosen_cadence_scale": scale,
                "l2_distance": dist,
                "score": score,
                "threshold": threshold,
                "modulation_subtle": scale <= 1.0,
            }
            found_subtle = True
            break
        if not found_subtle or dist < best_meta.get("l2_distance", 1e18):
            best_events = mod
            best_meta = {
                "evades_detector": score < threshold,
                "chosen_cadence_scale": scale,
                "l2_distance": dist,
                "score": score,
                "threshold": threshold,
                "modulation_subtle": scale <= 1.0,
            }

    if not best_meta.get("evades_detector"):
        best_meta["covert_capacity_below_op_point"] = (
            "≈zero — no cadence-scale modulation found that evades detector at this threshold"
        )
    return best_events, best_meta
