# Preliminary results caveats (carry forward to all gates)

**Status:** Phase 1 v1.2 **approved** to proceed to Phase 2. All inference and detector numbers below are **PRELIMINARY**.

**Do NOT use for:** external writeups, product/security claims, or Azure Phase 4 runs until the gating items below are satisfied.

## Gating items (Phase 1 → external / Azure)

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Report **single-draw** vs **40-draw-mean** observer accuracy/MI (label which is generous vs realistic) | Pipeline + report (re-run evaluate) |
| 2 | **Held-out-model** `model_class` / architecture generalization (not config memorization) | Extended corpus + `evaluate --held-out-model` |
| 3 | **Scale physical base captures** (`--repetitions-per-config`, `noise.py`); prominent real capture count; do not call augmented draws "runs" | Collect + terminology in stats |

## Terminology

| Term | Meaning |
|------|---------|
| **Physical base capture** | One `local-gpu` JSONL execution (unique `base_run_id`) |
| **Stochastic observation draw** | One application of `host_observer_realistic` transforms (up to N per base) |
| **Classifier sample** | One row for ML (often = one base capture, or one single draw — see report) |

## Phase 2

Detector (D2) metrics inherit the same **preliminary until scaled** caveat.
