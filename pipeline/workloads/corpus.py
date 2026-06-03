"""Labeled workload corpus — 10+ architectures, volume-matched train blocks for D2 hard case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

MIN_ARCHITECTURES_FOR_FINGERPRINT_CLAIM = 8

# Volume-matched train profile for cross-architecture detector hard case (same bs/seq/steps)
HARD_CASE_TRAIN_BS = 4
HARD_CASE_TRAIN_SL = 128
HARD_CASE_TRAIN_STEPS = 6

# (architecture_id, hidden, num_layers) — 10 distinct transfer signatures
ARCHITECTURE_SPECS: list[tuple[str, int, int]] = [
    ("arch_mlp_128x3", 128, 3),
    ("arch_mlp_256x4", 256, 4),
    ("arch_mlp_384x12", 384, 12),
    ("arch_mlp_512x6", 512, 6),
    ("arch_mlp_768x6", 768, 6),
    ("arch_mlp_1024x8", 1024, 8),
    ("arch_mlp_1280x8", 1280, 8),
    ("arch_mlp_1536x10", 1536, 10),
    ("arch_mlp_1920x10", 1920, 10),
    ("arch_mlp_2048x12", 2048, 12),
]


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    mode: str
    model_class: str  # legacy — do not use for fingerprint claims
    architecture_id: str
    batch_size: int
    seq_length: int
    llm_phase: str
    steps: int
    hidden: int
    num_layers: int
    vocab: int
    volume_profile: str = "standard"  # standard | hard_case_train


def _model_class_for_hidden(hidden: int) -> str:
    if hidden <= 256:
        return "small"
    if hidden <= 768:
        return "medium"
    return "large"


def iter_corpus() -> Iterator[WorkloadSpec]:
    """
    Per architecture: volume-matched train + infer, plus optional LLM phases on subset.
    """
    idx = 0
    for arch_id, hidden, layers in ARCHITECTURE_SPECS:
        mclass = _model_class_for_hidden(hidden)
        # Hard-case train block (same volume knobs across architectures)
        yield WorkloadSpec(
            workload_id=f"w{idx:02d}_train_{mclass}_n_a",
            mode="train",
            model_class=mclass,
            architecture_id=arch_id,
            batch_size=HARD_CASE_TRAIN_BS,
            seq_length=HARD_CASE_TRAIN_SL,
            llm_phase="n/a",
            steps=HARD_CASE_TRAIN_STEPS,
            hidden=hidden,
            num_layers=layers,
            vocab=32000,
            volume_profile="hard_case_train",
        )
        idx += 1
        # Infer (trivial mode violation for detector)
        yield WorkloadSpec(
            workload_id=f"w{idx:02d}_infer_{mclass}_n_a",
            mode="infer",
            model_class=mclass,
            architecture_id=arch_id,
            batch_size=1,
            seq_length=HARD_CASE_TRAIN_SL,
            llm_phase="n/a",
            steps=5,
            hidden=hidden,
            num_layers=layers,
            vocab=32000,
            volume_profile="standard",
        )
        idx += 1

    # Balanced batch/seq grid on every architecture (future collects)
    for arch_id, hidden, layers in ARCHITECTURE_SPECS:
        mclass = _model_class_for_hidden(hidden)
        for bs, sl in ((8, 128), (4, 256), (8, 256)):
            yield WorkloadSpec(
                workload_id=f"w{idx:02d}_train_{mclass}_bs{bs}_sl{sl}",
                mode="train",
                model_class=mclass,
                architecture_id=arch_id,
                batch_size=bs,
                seq_length=sl,
                llm_phase="n/a",
                steps=6,
                hidden=hidden,
                num_layers=layers,
                vocab=32000,
                volume_profile="standard",
            )
            idx += 1

    # LLM prefill/decode on all architectures (balanced llm_phase axis)
    for arch_id, hidden, layers in ARCHITECTURE_SPECS:
        mclass = _model_class_for_hidden(hidden)
        for phase, steps in [("prefill", 4), ("decode", 10)]:
            yield WorkloadSpec(
                workload_id=f"w{idx:02d}_infer_{mclass}_{phase}",
                mode="infer",
                model_class=mclass,
                architecture_id=arch_id,
                batch_size=1,
                seq_length=512,
                llm_phase=phase,
                steps=steps,
                hidden=hidden,
                num_layers=layers,
                vocab=50257,
                volume_profile="standard",
            )
            idx += 1


def corpus_size() -> int:
    return sum(1 for _ in iter_corpus())


def config_id_from_workload(workload_id: str) -> str:
    return workload_id.split("_s")[0].replace("/", "_")


def all_architecture_ids() -> list[str]:
    return [a[0] for a in ARCHITECTURE_SPECS]


def count_architectures_in_runs(labels_list: list) -> int:
    return len({lb.architecture_id or lb.model_class for lb in labels_list})
