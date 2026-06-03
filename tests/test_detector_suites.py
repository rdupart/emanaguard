"""Detector suite plumbing on synthetic runs."""

from __future__ import annotations

from detector.eval import ViolationSuite, run_detector_evaluation
from pipeline.backends.simulate import simulate_run
from pipeline.workloads.corpus import iter_corpus


def test_detector_returns_three_suites():
    runs = []
    for spec in list(iter_corpus())[:12]:
        runs.append(simulate_run(spec, 0, f"{spec.workload_id}_s0"))
    out = run_detector_evaluation(runs, backend="local-gpu-plumbing-test")
    assert "suites" in out
    assert "trivial_mode_change" in out["suites"]
    assert "hard_unauthorized_architecture" in out["suites"]
    assert "hard_covert_modulator_adaptive" in out["suites"]
    assert out["suites"]["trivial_mode_change"]["headline"] is False
    assert out["suites"]["hard_unauthorized_architecture"]["headline"] is True
    assert "detector_inference_audit" in out


def test_hard_wrong_arch_labels_train_only():
    from detector.eval import _suite_label
    from pipeline.trace.events import RunLabels

    benign = RunLabels(
        workload_id="w",
        mode="train",
        model_class="medium",
        batch_size=4,
        seq_length=128,
        llm_phase="n/a",
        seed=0,
        run_id="b1",
        architecture_id="arch_mlp_256x4",
        base_run_id="b1",
        config_id="c1",
        observation_idx=0,
    )
    viol = RunLabels(
        workload_id="w2",
        mode="train",
        model_class="medium",
        batch_size=4,
        seq_length=128,
        llm_phase="n/a",
        seed=0,
        run_id="b2",
        architecture_id="arch_mlp_512x6",
        base_run_id="b2",
        config_id="c2",
        observation_idx=0,
    )
    from detector.policy import AttestedPolicy

    pol = AttestedPolicy("p", frozenset({"train"}), frozenset({"arch_mlp_256x4"}))
    att = "arch_mlp_256x4"
    assert _suite_label(benign, ViolationSuite.HARD_WRONG_ARCH, pol, attested=att) == 0
    assert _suite_label(viol, ViolationSuite.HARD_WRONG_ARCH, pol, attested=att) == 1
