# PHASE 0 Report — Repository Cleanup (Step 0)

**Date:** 2026-06-03  
**Gate:** Human review before Phase 0.5  
**Action:** Undid merged application scaffolding on `main`; restored research-only tree.

---

## 1. What was removed

The following were **deleted** (previously introduced by merged PR #1 / `cursor/dev-environment-setup-c1b3`):

| Removed | Reason |
|---------|--------|
| `apps/` (Express API + Vite/React web) | Out of scope — not a research/data-pipeline repo |
| `packages/` (shared TS types) | Application monorepo |
| `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.npmrc` | Node/pnpm app tooling |
| `eslint.config.js`, `.gitignore` (app-oriented) | App tooling |
| `AGENTS.md` (Cloud dev-environment / `pnpm dev` instructions) | Wrong product |
| `PHASE_1_REPORT.md`, `PHASE_N_REPORT.md` | Incident-app / env-setup reports |

**Git on `main`:** Reset to pre-merge state (`cc96007`), then re-added only the three research assessment files from commit `7f1a4d7` on the old feature branch.

---

## 2. What was preserved

| File | Role |
|------|------|
| `README.md` | Repo title stub (to be replaced in a later phase with research runbook) |
| `related_work.md` | Literature survey |
| `novelty_assessment.md` | Prior novelty assessment (to be superseded in part by `delta_assessment.md` in Phase 0.5) |
| `cc_tenancy.md` | H100 CC tenancy / passthrough vs MIG |

---

## 3. Resulting file tree

```
.
├── README.md
├── related_work.md
├── novelty_assessment.md
├── cc_tenancy.md
└── PHASE_0_REPORT.md
```

**Confirmation:** No `package.json`, no `apps/`, no `packages/`, no Python pipeline yet (Phases 0.5+), no application or “hello world” code.

---

## 4. `main` branch history

- **Before:** `main` fast-forwarded to merge commit `5323b9f` (full emanaguard monorepo + env reports).
- **After:** `main` reset to `cc96007` + research markdown only (+ this report).

Remote `main` will be updated with a **force push** to drop the merge from the default branch (per “undo the last commit to main”).

---

## 5. Decision

| Item | Status |
|------|--------|
| Application code remains? | **No** |
| Proceed to Phase 0.5? | **Awaiting human approval** |

**Next (after approval):** Phase 0.5 — update `related_work.md`, add `delta_assessment.md`, `observer_feasibility.md`, then **STOP**.

---

## 6. Surprises / notes

- Research files (`related_work.md`, etc.) were **not** on `main` after the merge; they existed only on `cursor/dev-environment-setup-c1b3` at `7f1a4d7`. Restored from that commit.
- Local `node_modules/` from prior dev was removed from disk (never committed on clean tree).
