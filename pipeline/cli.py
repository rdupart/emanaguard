"""CLI: collect traces, evaluate, simulate smoke (plumbing only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.manifest import new_manifest


def cmd_collect(args: argparse.Namespace) -> int:
    seeds = [int(s) for s in args.seeds.split(",")]
    out_dir = Path(args.out_dir)

    if args.backend == "simulate":
        print("ERROR: simulate backend cannot collect publication traces.", file=sys.stderr)
        return 2
    if args.backend == "azure-cc":
        from pipeline.backends.azure_cc import raise_phase4_only

        raise_phase4_only()

    if args.backend != "local-gpu":
        print(f"Unknown backend: {args.backend}", file=sys.stderr)
        return 2

    from pipeline.backends.local_gpu import collect_to_dir

    manifest = new_manifest("local-gpu", seeds[0], extra={"seeds": seeds})
    manifest.write(out_dir / "manifest.json")
    paths = collect_to_dir(out_dir, seeds)
    print(f"Collected {len(paths)} runs -> {out_dir}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    if args.backend == "azure-cc":
        from pipeline.backends.azure_cc import raise_phase4_only

        raise_phase4_only()
    if args.backend == "simulate":
        print(
            "ERROR: evaluate with --backend simulate is disallowed for reported metrics.",
            file=sys.stderr,
        )
        return 2

    trace_dir = Path(args.trace_dir)
    seeds = [int(s) for s in args.seeds.split(",")]

    from pipeline.backends.local_gpu import load_or_collect
    from pipeline.eval.phase1_eval import run_evaluation

    runs = load_or_collect(trace_dir, seeds, force_collect=args.force_collect)
    if not runs:
        print(f"No traces in {trace_dir}. Run collect first.", file=sys.stderr)
        return 1

    bundle = run_evaluation(runs, backend=args.backend, seeds=seeds)
    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n")
    print(f"Wrote evaluation -> {out}")
    return 0


def cmd_smoke_simulate(args: argparse.Namespace) -> int:
    """End-to-end plumbing via simulate (not for publication numbers)."""
    from pipeline.backends.simulate import simulate_run
    from pipeline.eval.phase1_eval import run_evaluation
    from pipeline.workloads.corpus import iter_corpus

    seeds = [int(s) for s in args.seeds.split(",")]
    runs = []
    for seed in seeds:
        for spec in iter_corpus():
            run_id = f"{spec.workload_id}_s{seed}"
            runs.append(simulate_run(spec, seed, run_id))

    bundle = run_evaluation(runs, backend="simulate-PLUMBING-ONLY", seeds=seeds)
    print(json.dumps(bundle.to_dict(), indent=2))
    print(
        "\nNOTE: simulate output is NOT valid for PHASE_1_REPORT headline metrics.",
        file=sys.stderr,
    )
    return 0


def cmd_phase1(args: argparse.Namespace) -> int:
    """Full Phase 1: collect (local-gpu) + evaluate + write report stub paths."""
    trace_dir = Path(args.trace_dir)
    seeds = [int(s) for s in args.seeds.split(",")]
    results_json = Path(args.results_json)

    if args.backend != "local-gpu":
        print("phase1 command requires --backend local-gpu", file=sys.stderr)
        return 2

    rc = cmd_collect(argparse.Namespace(**{**vars(args), "out_dir": str(trace_dir)}))
    if rc != 0:
        return rc
    rc = cmd_evaluate(
        argparse.Namespace(
            backend="local-gpu",
            trace_dir=str(trace_dir),
            seeds=args.seeds,
            out_json=str(results_json),
            force_collect=False,
        )
    )
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="emanaguard Phase 1 pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="Collect traces")
    p_collect.add_argument("--backend", choices=["local-gpu", "simulate", "azure-cc"])
    p_collect.add_argument("--out-dir", default="data/traces/local-gpu")
    p_collect.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    p_collect.set_defaults(func=cmd_collect)

    p_eval = sub.add_parser("evaluate", help="Evaluate traces (local-gpu only for metrics)")
    p_eval.add_argument("--backend", choices=["local-gpu", "simulate", "azure-cc"])
    p_eval.add_argument("--trace-dir", default="data/traces/local-gpu")
    p_eval.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    p_eval.add_argument("--out-json", default="report/phase1_results.json")
    p_eval.add_argument("--force-collect", action="store_true")
    p_eval.set_defaults(func=cmd_evaluate)

    p_smoke = sub.add_parser("smoke-simulate", help="Plumbing smoke (not for publication)")
    p_smoke.add_argument("--seeds", default="0,1")
    p_smoke.set_defaults(func=cmd_smoke_simulate)

    p_p1 = sub.add_parser("phase1", help="Collect + evaluate local-gpu")
    p_p1.add_argument("--backend", default="local-gpu")
    p_p1.add_argument("--trace-dir", default="data/traces/local-gpu")
    p_p1.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    p_p1.add_argument("--results-json", default="report/phase1_results.json")
    p_p1.set_defaults(func=cmd_phase1)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
