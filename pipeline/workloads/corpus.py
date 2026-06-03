"""Labeled workload corpus specification for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    mode: str
    model_class: str
    batch_size: int
    seq_length: int
    llm_phase: str
    steps: int
    hidden: int
    vocab: int


def iter_corpus() -> Iterator[WorkloadSpec]:
    """Deterministic corpus — multiple runs use different seeds in runner."""
    configs = [
        # train vs infer, small vs large, varying batch/seq
        ("train", "small", 4, 128, "n/a", 8, 256, 32000),
        ("train", "small", 8, 128, "n/a", 8, 256, 32000),
        ("train", "large", 2, 128, "n/a", 6, 1024, 32000),
        ("train", "large", 4, 256, "n/a", 6, 1024, 32000),
        ("infer", "small", 1, 128, "n/a", 6, 256, 32000),
        ("infer", "small", 4, 128, "n/a", 6, 256, 32000),
        ("infer", "large", 1, 256, "n/a", 5, 1024, 32000),
        ("infer", "large", 2, 512, "n/a", 5, 1024, 32000),
        # LLM-like prefill vs decode (may be null on host-observer)
        ("infer", "small", 1, 512, "prefill", 4, 256, 50257),
        ("infer", "small", 1, 512, "decode", 12, 256, 50257),
        ("infer", "large", 1, 1024, "prefill", 3, 1024, 50257),
        ("infer", "large", 1, 1024, "decode", 16, 1024, 50257),
    ]
    for i, (mode, mclass, bs, sl, phase, steps, hidden, vocab) in enumerate(configs):
        yield WorkloadSpec(
            workload_id=f"w{i:02d}_{mode}_{mclass}_{phase}",
            mode=mode,
            model_class=mclass,
            batch_size=bs,
            seq_length=sl,
            llm_phase=phase,
            steps=steps,
            hidden=hidden,
            vocab=vocab,
        )


def corpus_size() -> int:
    return sum(1 for _ in iter_corpus())
