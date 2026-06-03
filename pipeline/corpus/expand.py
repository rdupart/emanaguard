"""Scale corpus via stochastic realistic-observer repetitions per base local-gpu capture."""

from __future__ import annotations

from dataclasses import replace

from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import config_id_from_workload


def enrich_labels(labels: RunLabels, base_run_id: str, observation_idx: int) -> RunLabels:
    machine_id = f"m{labels.seed % 4}_{observation_idx % 3}"
    return replace(
        labels,
        config_id=config_id_from_workload(labels.workload_id),
        base_run_id=base_run_id,
        observation_idx=observation_idx,
        machine_id=machine_id,
        run_id=f"{base_run_id}_obs{observation_idx:03d}",
    )


def expand_observations(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    observations_per_base: int,
    global_seed: int = 0,
) -> list[tuple[list[TransferEvent], RunLabels]]:
    """
    Each base JSONL capture yields K host-observation samples (stochastic transform).
    Labels unchanged; features vary — models repeated host observations of same job.
    """
    expanded: list[tuple[list[TransferEvent], RunLabels]] = []
    for events, labels in runs:
        base_run_id = labels.run_id
        labels = enrich_labels(labels, base_run_id, 0)
        for obs_idx in range(observations_per_base):
            new_labels = enrich_labels(labels, base_run_id, obs_idx)
            expanded.append((events, new_labels))
    return expanded


def corpus_statistics(
    runs: list[tuple[list[TransferEvent], RunLabels]],
) -> dict:
    configs: dict[str, int] = {}
    base_runs: set[str] = set()
    for _, lb in runs:
        cid = getattr(lb, "config_id", None) or config_id_from_workload(lb.workload_id)
        configs[cid] = configs.get(cid, 0) + 1
        base_runs.add(getattr(lb, "base_run_id", lb.run_id))
    return {
        "total_runs": len(runs),
        "unique_base_captures": len(base_runs),
        "num_configs": len(configs),
        "runs_per_config": configs,
        "mean_runs_per_config": len(runs) / max(len(configs), 1),
    }
