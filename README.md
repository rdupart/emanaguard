# emanaguard

Research repository: **host-observable I/O metadata at the NVIDIA H100 Confidential Computing boundary** (SL5-oriented, defensive).

## Status

| Phase | Gate report | Status |
|-------|-------------|--------|
| Step 0 | `PHASE_0_REPORT.md` | Approved |
| 0.5 | `PHASE_0.5_REPORT.md` | **Awaiting review** |
| 1 | `PHASE_1_REPORT.md` | Not started |

## Key documents

- `related_work.md` — literature (incl. Phase 0.5 surveys)
- `delta_assessment.md` — D1–D4 vs arXiv:2507.02770
- `observer_feasibility.md` — measurement plan (`simulate` / `local-gpu` / `azure-cc`)
- `cc_tenancy.md` — H100 CC passthrough vs MIG

**Scope:** Python research pipeline only (no web app). Extends arXiv:2507.02770; we do **not** claim discovery of the CPU–GSP timing channel.
