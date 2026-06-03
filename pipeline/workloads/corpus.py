"""Labeled workload corpus — configs, architectures, collection specs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    mode: str
    model_class: str  # legacy bucket: small | large | medium | wide
    architecture_id: str  # held-out-model split key
    batch_size: int
    seq_length: int
    llm_phase: str
    steps: int
    hidden: int
    num_layers: int
    vocab: int


def iter_corpus() -> Iterator[WorkloadSpec]:
    """12 baseline configs + 4 extra architectures for held-out-model validation."""
    configs = [
        # (mode, model_class, arch_id, bs, sl, phase, steps, hidden, layers, vocab)
        ("train", "small", "arch_mlp_256x4", 4, 128, "n/a", 8, 256, 4, 32000),
        ("train", "small", "arch_mlp_256x4", 8, 128, "n/a", 8, 256, 4, 32000),
        ("train", "large", "arch_mlp_1024x8", 2, 128, "n/a", 6, 1024, 8, 32000),
        ("train", "large", "arch_mlp_1024x8", 4, 256, "n/a", 6, 1024, 8, 32000),
        ("infer", "small", "arch_mlp_256x4", 1, 128, "n/a", 6, 256, 4, 32000),
        ("infer", "small", "arch_mlp_256x4", 4, 128, "n/a", 6, 256, 4, 32000),
        ("infer", "large", "arch_mlp_1024x8", 1, 256, "n/a", 5, 1024, 8, 32000),
        ("infer", "large", "arch_mlp_1024x8", 2, 512, "n/a", 5, 1024, 8, 32000),
        ("infer", "small", "arch_mlp_256x4", 1, 512, "prefill", 4, 256, 4, 50257),
        ("infer", "small", "arch_mlp_256x4", 1, 512, "decode", 12, 256, 4, 50257),
        ("infer", "large", "arch_mlp_1024x8", 1, 1024, "prefill", 3, 1024, 8, 50257),
        ("infer", "large", "arch_mlp_1024x8", 1, 1024, "decode", 16, 1024, 8, 50257),
        # Additional architectures (for held-out-model eval; collect on GPU)
        ("infer", "medium", "arch_mlp_512x6", 2, 128, "n/a", 5, 512, 6, 32000),
        ("infer", "wide", "arch_mlp_384x12", 2, 128, "n/a", 5, 384, 12, 32000),
        ("train", "medium", "arch_mlp_512x6", 4, 128, "n/a", 6, 512, 6, 32000),
        ("infer", "xlarge", "arch_mlp_1536x10", 1, 128, "n/a", 4, 1536, 10, 32000),
    ]
    for i, row in enumerate(configs):
        mode, mclass, arch, bs, sl, phase, steps, hidden, layers, vocab = row
        yield WorkloadSpec(
            workload_id=f"w{i:02d}_{mode}_{mclass}_{phase}".replace("n/a", "n_a"),
            mode=mode,
            model_class=mclass,
            architecture_id=arch,
            batch_size=bs,
            seq_length=sl,
            llm_phase=phase,
            steps=steps,
            hidden=hidden,
            num_layers=layers,
            vocab=vocab,
        )


def corpus_size() -> int:
    return sum(1 for _ in iter_corpus())


def config_id_from_workload(workload_id: str) -> str:
    return workload_id.split("_s")[0].replace("/", "_")


def all_architecture_ids() -> list[str]:
    return sorted({s.architecture_id for s in iter_corpus()})
