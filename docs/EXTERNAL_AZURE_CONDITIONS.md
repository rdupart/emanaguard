# Conditions gating external claims and Azure Phase 4

Phase 3 (mitigation) is **approved locally**. These items gate **external writeups** and **Azure Phase 4**, not in-repo Phase 3 development.

| # | Condition | Status |
|---|-----------|--------|
| 1 | **llm_phase NULL rationale** documented as volume-confound + minority fragility (not “fails majority”) | Code + `gate_summary.llm_phase_null_rationale` |
| 2 | **Detector honesty** — volume-level suite + bytes-matched timing suite; balanced vs majority with weak-margin callout | `phase2_results.json` suites |
| 3 | **Covert capacity** — FPR/operating point + adaptive below-threshold search; heavy AUC not headline | `hard_covert_modulator_adaptive` |
| 4 | **Phase 3 mitigation** — padding + constant-RPC measured on mode/batch_size | `phase3_results.json` |

Azure CC backend remains **unimplemented** until these are satisfied for publication scope.
