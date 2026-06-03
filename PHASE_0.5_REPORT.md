# PHASE 0.5 Report — Targeted Novelty + Feasibility

**Date:** 2026-06-03  
**Gate:** Human review before **Phase 1** (workload-inference pipeline)  
**Prerequisite:** Step 0 approved (`PHASE_0_REPORT.md`)

---

## 1. Deliverables completed

| File | Status |
|------|--------|
| `related_work.md` (Phase 0.5 addendum: surveys a–c) | Updated |
| `delta_assessment.md` | Created |
| `observer_feasibility.md` | Created |
| `PHASE_0.5_REPORT.md` | This file |

**Not created (per scope fence):** `package.json`, `pipeline/`, `requirements.txt`, application code, Azure resources.

---

## 2. Novelty delta (explicit vs arXiv:2507.02770)

| Delta | Claim we **do not** make | Claim we **do** make |
|-------|--------------------------|----------------------|
| **D1** | “First timing side channel under GPU-CC” | **Workload inference** (multi-axis labels) from **host-visible** I/O metadata, with measured accuracy/MI |
| **D2** | “First GPU anomaly detector” | **Policy deviation** vs **attested** workload on **same** telemetry |
| **D3** | “Invented constant-time RPC” | **Evaluate** their mitigations: leakage vs overhead |
| **D4** | “New SL5 standard” | **Focused 800-53 diff** for CC I/O observability under SL5 v0.1 parent |

**Honest weakness:** D1 fine labels (prefill vs decode) may be **infeasible**; Phase 1 must report MI/confusion honestly.

---

## 3. Feasibility summary (`observer_feasibility.md`)

| Backend | When | Role |
|---------|------|------|
| `simulate` | Phase 1–3 on laptop | Full pipeline without GPU |
| `local-gpu` | Phase 1–3 on cheap GPU | Labeled corpus + ground-truth traces |
| `azure-cc` | Phase 4 only (post-approval) | Validate signals & metric transfer under CC-On |

**Minimum viable measurement (no kernel hack):** Python victim runner logs copy events → post-process to observer features.

---

## 4. Surprises

1. **Only one clear CC-on predecessor** for our path: arXiv:2507.02770—reduces literature sprawl but raises reviewer bar (“incremental?”).
2. **SL5 v0.1 already exists**—D4 must be a **diff**, not a parallel standard.
3. **“AI705”** still **UNVERIFIED** as published control catalog name.

---

## 5. Decision

| Item | Recommendation |
|------|----------------|
| Proceed to Phase 1? | **Yes**, if human approves |
| Azure before Phase 1–3? | **No** (per project rules) |
| First Phase 1 code | `requirements.txt`, `pipeline/`, `--backend simulate`, workload corpus spec |

---

## 6. File tree (after Phase 0.5)

```
.
├── README.md
├── related_work.md
├── novelty_assessment.md          # legacy; superseded for deltas by delta_assessment.md
├── cc_tenancy.md
├── delta_assessment.md            # NEW
├── observer_feasibility.md        # NEW
├── PHASE_0_REPORT.md
└── PHASE_0.5_REPORT.md            # NEW
```

---

**STOP — awaiting human approval before Phase 1.**
