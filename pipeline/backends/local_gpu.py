"""local-gpu backend — real CUDA transfer traces (non-CC proxy for host-observer)."""

from __future__ import annotations

from pathlib import Path

from pipeline.manifest import new_manifest
from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.trace.io import load_trace_dir, write_run
from pipeline.workloads.corpus import WorkloadSpec, iter_corpus
from pipeline.workloads.runner import run_workload


def collect_to_dir(
    out_dir: Path,
    seeds: list[int],
) -> list[Path]:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(
            "local-gpu collection requires CUDA (nvidia-smi + CUDA PyTorch). "
            "Run on Colab/RunPod/bare-metal GPU; simulate is for tests only."
        )

    paths: list[Path] = []
    for seed in seeds:
        manifest = new_manifest("local-gpu", seed, extra={"out_dir": str(out_dir)})
        manifest.write(out_dir / f"manifest_seed{seed}.json")
        for spec in iter_corpus():
            run_id = f"{spec.workload_id}_s{seed}"
            events, labels = run_workload(spec, seed, run_id)
            paths.append(write_run(out_dir, events, labels))
    return paths


def load_or_collect(
    trace_dir: Path,
    seeds: list[int],
    force_collect: bool = False,
) -> list[tuple[list[TransferEvent], RunLabels]]:
    if force_collect or not any(trace_dir.glob("*.jsonl")):
        collect_to_dir(trace_dir, seeds)
    return load_trace_dir(trace_dir)
