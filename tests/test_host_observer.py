"""Tests for host-observer projection — no label leakage in simulate plumbing."""

from __future__ import annotations

from pipeline.backends.simulate import synthetic_events_for_test
from pipeline.features.host_observer import host_observer_feature_vector, project_host_observer
from pipeline.trace.events import TransferEvent


def test_projection_strips_vm_fields():
    events = synthetic_events_for_test(seed=1)
    host = project_host_observer(events)
    assert all("op_name" not in e for e in host)
    assert all("phase" not in e for e in host)
    assert all("stream_id" not in e for e in host)


def test_host_features_deterministic():
    events = synthetic_events_for_test(seed=2)
    host = project_host_observer(events)
    a = host_observer_feature_vector(host)
    b = host_observer_feature_vector(host)
    assert (a == b).all()


def test_vm_event_has_extra_fields():
    e = synthetic_events_for_test(1, seed=0)[0]
    assert isinstance(e, TransferEvent)
    assert e.op_name is not None
