# Preliminary results caveats (carry forward to all gates)

**Status:** Phase 1 methodology v1.3 is acceptable; **Phase 3 is NOT approved** until corpus scale, labeling audit, held-out-model, and hard-case detector gates pass.

**Do NOT use for:** external writeups, product/security claims, “model fingerprinting,” or Azure Phase 4 runs until the gating items below are satisfied.

## Gating items (Phase 1 → external / Azure)

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Report **single-draw** vs **40-draw-mean** observer accuracy/MI (label which is generous vs realistic) | In pipeline + report |
| 2 | **Labeling audit:** explain `architecture_id` vs `model_class`; **retract** `model_class`; do not cite `architecture_id` as positive until **≥8 physical architectures** | `docs/architecture_labeling_audit.md` + JSON `architecture_labeling_audit` |
| 3 | **Held-out-model:** single-draw, hold out entire unseen `architecture_id`s; honest negative if no generalization | `held_out_model_evaluation` in evaluate output |
| 4 | **≥8–10 distinct architectures** in physical captures (corpus spec has 10; re-collect required) | Collect on `cursor/phase-2-detector-c1b3` corpus |
| 5 | **Scale physical base captures** (`--repetitions-per-config`, `noise.py`); do not call augmented draws “runs” | Collect + terminology in stats |
| 6 | **Detector D2 hard case:** ROC for (a) wrong arch same volume, (b) covert modulator — **separate** from trivial mode-change AUC | `detect` → `suites` in phase2 JSON |

## Terminology

| Term | Meaning |
|------|---------|
| **Physical base capture** | One `local-gpu` JSONL execution (unique `base_run_id`) |
| **Stochastic observation draw** | One application of `host_observer_realistic` transforms (up to N per base) |
| **Classifier sample** | One row for ML (often = one base capture, or one single draw — see report) |

## Phase 2

- **Headline:** `hard_unauthorized_architecture` + `hard_covert_modulator` ROC AUC.
- **Not a result:** `trivial_mode_change` (mode/volume only).
- Detector metrics inherit the same **preliminary until scaled** caveat as Phase 1.
