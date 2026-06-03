"""Execute labeled workloads and record transfer events (local-gpu)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np
import torch

from pipeline.trace.events import Direction, RunLabels, TransferEvent
from pipeline.workloads.corpus import WorkloadSpec, config_id_from_workload

if TYPE_CHECKING:
    pass


class TransferRecorder:
    """Records H↔D copies with in-VM metadata (stripped later for host-observer)."""

    def __init__(
        self,
        run_id: str,
        device: torch.device,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.run_id = run_id
        self.device = device
        self.rng = rng
        self.events: list[TransferEvent] = []

    def h2d(
        self,
        cpu_tensor: torch.Tensor,
        op_name: str,
        phase: str,
        stream: int = 0,
    ) -> torch.Tensor:
        if self.rng is not None:
            from pipeline.workloads.noise import collection_jitter_sleep

            collection_jitter_sleep(self.rng)
        t0 = time.perf_counter_ns()
        gpu = cpu_tensor.to(self.device, non_blocking=False)
        torch.cuda.synchronize()
        t1 = time.perf_counter_ns()
        self.events.append(
            TransferEvent(
                t_ns=t0,
                size_bytes=cpu_tensor.numel() * cpu_tensor.element_size(),
                direction=Direction.H2D,
                duration_ns=t1 - t0,
                op_name=op_name,
                stream_id=stream,
                phase=phase,
                run_id=self.run_id,
            )
        )
        return gpu

    def d2h(
        self,
        gpu_tensor: torch.Tensor,
        op_name: str,
        phase: str,
        stream: int = 0,
    ) -> torch.Tensor:
        if self.rng is not None:
            from pipeline.workloads.noise import collection_jitter_sleep

            collection_jitter_sleep(self.rng)
        t0 = time.perf_counter_ns()
        cpu = gpu_tensor.detach().cpu()
        torch.cuda.synchronize()
        t1 = time.perf_counter_ns()
        self.events.append(
            TransferEvent(
                t_ns=t0,
                size_bytes=gpu_tensor.numel() * gpu_tensor.element_size(),
                direction=Direction.D2H,
                duration_ns=t1 - t0,
                op_name=op_name,
                stream_id=stream,
                phase=phase,
                run_id=self.run_id,
            )
        )
        return cpu


def _linear_block(
    recorder: TransferRecorder,
    spec: WorkloadSpec,
    phase: str,
    train: bool,
) -> None:
    hidden = spec.hidden
    batch = spec.batch_size
    seq = spec.seq_length
    layers = 4 if spec.model_class == "small" else 8

    x_cpu = torch.randn(batch, seq, hidden)
    x = recorder.h2d(x_cpu, "input_activation", phase)

    for li in range(layers):
        w_cpu = torch.randn(hidden, hidden)
        w = recorder.h2d(w_cpu, f"load_weights_l{li}", phase)
        x = torch.matmul(x, w)
        torch.cuda.synchronize()
        if train:
            grad_cpu = torch.randn(batch, seq, hidden)
            recorder.h2d(grad_cpu, f"grad_in_l{li}", phase)
            recorder.d2h(x, f"grad_out_l{li}", phase)

    recorder.d2h(x, "output_activation", phase)


def _llm_prefill_decode(recorder: TransferRecorder, spec: WorkloadSpec) -> None:
    hidden = spec.hidden
    batch = 1
    seq = spec.seq_length
    vocab = min(spec.vocab, 8192)
    device = recorder.device

    emb_cpu = torch.randn(vocab, hidden)
    emb = recorder.h2d(emb_cpu, "load_embedding", spec.llm_phase)

    if spec.llm_phase == "prefill":
        idx = torch.randint(0, vocab, (batch, seq), device=device)
        x = emb[idx]
        for _ in range(3):
            w_cpu = torch.randn(hidden, hidden)
            w = recorder.h2d(w_cpu, "load_attn", "prefill")
            x = torch.matmul(x, w)
        torch.cuda.synchronize()
        recorder.d2h(x, "prefill_out", "prefill")
    else:
        for _ in range(spec.steps):
            token = torch.randint(0, vocab, (batch, 1), device=device)
            x = emb[token.squeeze(0)]
            w_cpu = torch.randn(hidden, hidden)
            w = recorder.h2d(w_cpu, "load_decode", "decode")
            x = torch.matmul(x, w)
            torch.cuda.synchronize()
            recorder.d2h(x, "decode_token", "decode")


def run_workload(
    spec: WorkloadSpec,
    seed: int,
    run_id: str,
    device: torch.device | None = None,
    *,
    enable_noise: bool = True,
    repetition: int = 0,
) -> tuple[list[TransferEvent], RunLabels]:
    torch.manual_seed(seed + repetition * 9973)
    rng = np.random.default_rng(seed + repetition * 17) if enable_noise else None
    if device is None:
        if not torch.cuda.is_available():
            raise RuntimeError(
                "local-gpu backend requires CUDA. No GPU in this environment."
            )
        device = torch.device("cuda")

    bg = None
    if enable_noise and rng is not None:
        from pipeline.workloads.noise import BackgroundGpuLoad

        bg = BackgroundGpuLoad(device, rng)
        bg.start()

    recorder = TransferRecorder(run_id, device, rng=rng)
    labels = RunLabels(
        workload_id=spec.workload_id,
        mode=spec.mode,
        model_class=spec.model_class,
        batch_size=spec.batch_size,
        seq_length=spec.seq_length,
        llm_phase=spec.llm_phase,
        seed=seed,
        run_id=run_id,
        config_id=config_id_from_workload(spec.workload_id),
        base_run_id=run_id,
        observation_idx=repetition,
        machine_id=f"coloc_{seed % 4}",
    )

    try:
        if spec.llm_phase in ("prefill", "decode"):
            _llm_prefill_decode(recorder, spec)
        else:
            for _ in range(spec.steps):
                phase = "train_step" if spec.mode == "train" else "infer_step"
                _linear_block(recorder, spec, phase, train=(spec.mode == "train"))
    finally:
        if bg is not None:
            bg.stop()

    return recorder.events, labels
