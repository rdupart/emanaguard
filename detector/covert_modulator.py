"""
Tier-Red style covert timing/size modulation on host-observer events.

Measurement-only transforms for D2 evaluation — not an attack tool.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable

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

FEATURE_NOISE_L2 = 1e-9


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
    """Fine-grained strength via cadence multiplier (continuous amplitude axis)."""
    base = MODULATION_PRESETS["light"]
    return apply_covert_modulator(
        host_events,
        rng,
        cadence_ns=max(1, int(base.cadence_ns * cadence_scale)),
        jitter_fraction=jitter_fraction,
        strength=None,
    )


def sweep_cadence_amplitude_curve(
    host_events: list[dict],
    rng: np.random.Generator,
    benign_feature_vector: np.ndarray,
    feature_fn: Callable[[list[dict]], np.ndarray],
    violation_score_fn: Callable[[list[dict]], float],
    *,
    threshold: float,
    scale_min: float = 0.02,
    scale_max: float = 4.0,
    n_steps: int = 48,
) -> list[dict]:
    """
    Continuous cadence-amplitude sweep: detectability vs modulation strength.

    Each point: cadence_scale, detector score, L2 feature delta, evades threshold.
  Stops reporting meaningful signal below FEATURE_NOISE_L2 (noise floor).
    """
    scales = np.linspace(scale_min, scale_max, n_steps)
    curve: list[dict] = []
    for scale in scales:
        mod = apply_covert_modulator_scaled(host_events, rng, cadence_scale=float(scale))
        feat = feature_fn(mod)
        dist = float(np.linalg.norm(feat - benign_feature_vector))
        score = float(violation_score_fn(mod))
        below_noise = dist < FEATURE_NOISE_L2
        curve.append(
            {
                "cadence_scale": float(scale),
                "l2_distance": dist,
                "score": score,
                "evades_detector": score < threshold and not below_noise,
                "below_feature_noise_floor": below_noise,
            }
        )
    return curve


def aggregate_amplitude_sweep(
    per_trace_curves: list[list[dict]],
    *,
    threshold: float,
) -> dict:
    """Aggregate per-trace sweeps into capacity-vs-detectability summary."""
    if not per_trace_curves:
        return {
            "n_traces": 0,
            "suite_interpretation": "UNTESTABLE — no attested test traces for sweep",
        }

    scales = sorted({p["cadence_scale"] for c in per_trace_curves for p in c})
    aggregated: list[dict] = []
    for s in scales:
        evade = 0
        detected = 0
        noise = 0
        n = 0
        scores: list[float] = []
        dists: list[float] = []
        for curve in per_trace_curves:
            pt = next((p for p in curve if p["cadence_scale"] == s), None)
            if pt is None:
                continue
            n += 1
            scores.append(pt["score"])
            dists.append(pt["l2_distance"])
            if pt["below_feature_noise_floor"]:
                noise += 1
            elif pt["evades_detector"]:
                evade += 1
            else:
                detected += 1
        aggregated.append(
            {
                "cadence_scale": s,
                "n_traces": n,
                "fraction_evading": evade / max(n, 1),
                "fraction_detected": detected / max(n, 1),
                "fraction_below_noise_floor": noise / max(n, 1),
                "mean_score": float(np.mean(scores)) if scores else 0.0,
                "mean_l2_distance": float(np.mean(dists)) if dists else 0.0,
            }
        )

    any_evasion = any(
        p["evades_detector"] for c in per_trace_curves for p in c
    )
    min_evasion_scale: float | None = None
    for c in per_trace_curves:
        for p in c:
            if p["evades_detector"]:
                sc = p["cadence_scale"]
                if min_evasion_scale is None or sc < min_evasion_scale:
                    min_evasion_scale = sc

    if any_evasion:
        cap_claim = (
            f"Some cadence scales evade at operating threshold (min_scale≈{min_evasion_scale})"
        )
    else:
        cap_claim = (
            "Tested continuous cadence sweep (0.02–4.0× light baseline): no scale evades "
            "detector at operating point on held-out attested traces; "
            "adaptive-adversary covert capacity NOT established (preset-only evasion search retired)."
        )

    return {
        "n_traces": len(per_trace_curves),
        "operating_threshold": threshold,
        "curve": aggregated,
        "any_evasion_in_sweep": any_evasion,
        "min_evasion_cadence_scale": min_evasion_scale,
        "covert_capacity_claim": cap_claim,
        "preset_adaptive_note": (
            "Three-preset adaptive search is not used for capacity claims; "
            "see continuous amplitude curve."
        ),
    }


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
    Legacy discrete-scale search (per-trace). Prefer sweep_cadence_amplitude_curve + aggregate.
    """
    curve = sweep_cadence_amplitude_curve(
        host_events,
        rng,
        benign_feature_vector,
        feature_fn,
        violation_score_fn,
        threshold=threshold,
        scale_min=min(cadence_scales),
        scale_max=max(cadence_scales),
        n_steps=len(cadence_scales),
    )
    evading = [p for p in curve if p["evades_detector"]]
    if evading:
        best = evading[0]
        best_events = apply_covert_modulator_scaled(
            host_events, rng, cadence_scale=best["cadence_scale"]
        )
        return best_events, {
            "evades_detector": True,
            "chosen_cadence_scale": best["cadence_scale"],
            "l2_distance": best["l2_distance"],
            "score": best["score"],
            "threshold": threshold,
            "legacy_discrete_search": True,
        }
    last = curve[-1] if curve else {}
    return host_events, {
        "evades_detector": False,
        "chosen_cadence_scale": last.get("cadence_scale", 0.0),
        "l2_distance": last.get("l2_distance", 0.0),
        "score": last.get("score", 1.0),
        "threshold": threshold,
        "legacy_discrete_search": True,
    }
