"""Phase 3 overhead and pad-up semantics."""

from __future__ import annotations

import numpy as np

from pipeline.features.realistic_observer import STAGING_BLOCK_BYTES, apply_realistic_observer
from pipeline.mitigation.feature_shim import mitigate_size_padding_observer


def test_size_padding_never_shrinks_observer_bytes():
    obs = [
        {"t_ns": 0, "size_bytes": 50_000, "direction": "h2d"},
        {"t_ns": 1000, "size_bytes": 8_192, "direction": "d2h"},
    ]
    mit = mitigate_size_padding_observer(obs)
    base_total = sum(e["size_bytes"] for e in obs)
    mit_total = sum(e["size_bytes"] for e in mit)
    assert mit_total >= base_total
    assert all(e["size_bytes"] >= STAGING_BLOCK_BYTES for e in mit)


def test_size_padding_ratio_on_observer_path():
    rng = np.random.default_rng(0)
    host = [
        {"t_ns": i * 1000, "size_bytes": 512 * (i + 1), "direction": "h2d"}
        for i in range(8)
    ]
    obs = apply_realistic_observer(host, rng)
    mit = mitigate_size_padding_observer(obs)
    ratio = sum(e["size_bytes"] for e in mit) / max(
        sum(e["size_bytes"] for e in obs), 1
    )
    assert ratio >= 1.0
