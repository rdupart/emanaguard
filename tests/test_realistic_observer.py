from __future__ import annotations

import numpy as np

from pipeline.backends.simulate import synthetic_events_for_test
from pipeline.features.host_observer import project_host_observer
from pipeline.features.realistic_observer import (
    apply_realistic_observer,
    realistic_observer_features,
    volume_only_features,
)


def test_realistic_differs_from_idealized():
    events = synthetic_events_for_test(50, seed=1)
    host = project_host_observer(events)
    rng = np.random.default_rng(99)
    ideal = realistic_observer_features(host, np.random.default_rng(0))
    real = realistic_observer_features(host, rng)
    assert not np.allclose(ideal, real)


def test_stochastic_observations_differ():
    host = project_host_observer(synthetic_events_for_test(30, seed=2))
    a = realistic_observer_features(host, np.random.default_rng(1))
    b = realistic_observer_features(host, np.random.default_rng(2))
    assert not np.allclose(a, b)


def test_volume_ablation_smaller_dim():
    host = project_host_observer(synthetic_events_for_test(20, seed=3))
    v = volume_only_features(host, np.random.default_rng(0))
    assert v.shape == (4,)


def test_quantization_hides_exact_size():
    host = [{"t_ns": 0, "size_bytes": 525000, "direction": "H2D", "duration_ns": 1000}]
    obs = apply_realistic_observer(host, np.random.default_rng(0))
    assert obs[0]["size_bytes"] != 525000
