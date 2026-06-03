"""Total-bytes-matched subsets for honest detector evaluation."""

from __future__ import annotations

import numpy as np

FEAT_TOTAL_BYTES = 1


def total_bytes_from_features(x: np.ndarray) -> float:
    return float(x[FEAT_TOTAL_BYTES])


def match_bytes_pairs(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    *,
    relative_tolerance: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Pair each violation row with nearest benign row on total_bytes (within tolerance).
    """
    benign_idx = np.where(y == 0)[0]
    viol_idx = np.where(y == 1)[0]
    if len(benign_idx) == 0 or len(viol_idx) == 0:
        return (
            np.empty((0, x.shape[1])),
            np.array([], dtype=int),
            np.array([], dtype=object),
            {"status": "empty", "n_pairs": 0},
        )

    b_bytes = x[benign_idx, FEAT_TOTAL_BYTES]
    kept_x, kept_y, kept_g = [], [], []
    n_pairs = 0
    rel_errors = []
    for vi in viol_idx:
        vb = x[vi, FEAT_TOTAL_BYTES]
        j = int(np.argmin(np.abs(b_bytes - vb)))
        bi = benign_idx[j]
        bb = b_bytes[j]
        rel = abs(vb - bb) / max(abs(bb), 1.0)
        if rel > relative_tolerance:
            continue
        rel_errors.append(rel)
        kept_x.append(x[bi])
        kept_y.append(0)
        kept_g.append(groups[bi])
        kept_x.append(x[vi])
        kept_y.append(1)
        kept_g.append(groups[vi])
        n_pairs += 1

    meta = {
        "status": "ok" if kept_x else "no_pairs_within_tolerance",
        "n_pairs": n_pairs,
        "relative_tolerance": relative_tolerance,
        "mean_relative_bytes_error": float(np.mean(rel_errors)) if rel_errors else None,
        "n_benign_pool": len(benign_idx),
        "n_violation": len(viol_idx),
    }
    if not kept_x:
        return np.empty((0, x.shape[1])), np.array([], dtype=int), np.array([], dtype=object), meta
    return np.vstack(kept_x), np.array(kept_y), np.array(kept_g), meta


def timing_structure_features(x: np.ndarray) -> np.ndarray:
    """Drop coarse volume scalars; keep cadence/shape dimensions for bytes-matched test."""
    drop = {0, 1, 2}
    keep = [j for j in range(x.shape[1]) if j not in drop]
    return x[:, keep] if keep else x
