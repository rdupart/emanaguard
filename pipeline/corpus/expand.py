"""Scale corpus via stochastic realistic-observer repetitions per physical base capture."""

from __future__ import annotations

from dataclasses import replace

from pipeline.trace.events import RunLabels, TransferEvent
from pipeline.workloads.corpus import config_id_from_workload


def enrich_labels(labels: RunLabels, base_run_id: str, observation_idx: int) -> RunLabels:
    machine_id = f"m{labels.seed % 4}_{observation_idx % 3}"
    arch = labels.architecture_id or labels.model_class
    return replace(
        labels,
        config_id=config_id_from_workload(labels.workload_id),
        base_run_id=base_run_id,
        observation_idx=observation_idx,
        machine_id=machine_id,
        architecture_id=arch,
    )


def expand_observations(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    observations_per_base: int,
    global_seed: int = 0,
    *,
    single_draw_only: bool = False,
) -> list[tuple[list[TransferEvent], RunLabels]]:
    """
    Expand each physical base capture into stochastic observation draws.
    If single_draw_only, keep observation_idx=0 only (realistic adversary).
    """
    expanded: list[tuple[list[TransferEvent], RunLabels]] = []
    n_draws = 1 if single_draw_only else observations_per_base
    for events, labels in runs:
        base_run_id = labels.run_id
        for obs_idx in range(n_draws):
            expanded.append((events, enrich_labels(labels, base_run_id, obs_idx)))
    return expanded


def corpus_statistics(
    runs: list[tuple[list[TransferEvent], RunLabels]],
    *,
    observations_per_base: int = 1,
    single_draw: bool = False,
) -> dict:
    configs: dict[str, int] = {}
    base_runs: set[str] = set()
    for _, lb in runs:
        cid = getattr(lb, "config_id", None) or config_id_from_workload(lb.workload_id)
        configs[cid] = configs.get(cid, 0) + 1
        base_runs.add(getattr(lb, "base_run_id", lb.run_id))

    n_base = len(base_runs)
    n_obs = len(runs)
    if single_draw:
        obs_label = "single_draw_per_base"
    else:
        obs_label = "stochastic_observation_draws"

    return {
        "physical_base_captures": n_base,
        "stochastic_observation_draws": n_obs,
        "observations_per_base_capture": 1 if single_draw else observations_per_base,
        "num_configs": len(configs),
        "observation_draws_per_config": configs,
        "mean_draws_per_config": n_obs / max(len(configs), 1),
        # legacy keys for tooling
        "unique_base_captures": n_base,
        "total_runs": n_obs,
        "runs_per_config": configs,
        "terminology_note": (
            f"'{obs_label}' are NOT additional GPU executions; "
            "only physical_base_captures are real local-gpu collects."
        ),
    }
