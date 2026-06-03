"""Collection-time noise: background GPU load and timing jitter (local-gpu)."""

from __future__ import annotations

import threading
import time

import numpy as np
import torch


class BackgroundGpuLoad:
    """Co-located contention — extra PCIe/memcpy traffic unrelated to victim labels."""

    def __init__(self, device: torch.device, rng: np.random.Generator) -> None:
        self.device = device
        self.rng = rng
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        def _loop() -> None:
            while not self._stop.is_set():
                n = int(self.rng.integers(256, 2048))
                x = torch.randn(n, n, device=self.device)
                _ = x @ x
                torch.cuda.synchronize()
                time.sleep(float(self.rng.uniform(0.001, 0.015)))

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


def collection_jitter_sleep(rng: np.random.Generator) -> None:
    """Host scheduling / CVM timer noise before transfers."""
    time.sleep(float(rng.uniform(0.0, 4e-3)))
