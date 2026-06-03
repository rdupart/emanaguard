# Phase 1 Report — Development Environment Setup

**Project:** emanaguard  
**Phase:** 1 — Development environment setup  
**Date:** 2026-06-03  
**Branch:** `cursor/dev-environment-setup-c1b3`  
**PR:** https://github.com/rdupart/emanaguard/pull/1  

---

## 1. Phase objective

Establish a reproducible local and Cloud Agent development environment: install dependencies, document how to run services, verify lint/test/build, run the application, and complete an end-to-end “hello world” incident workflow.

---

## 2. Repository state

### Before

| Item | Status |
|------|--------|
| Application code | None (README title only) |
| Package manager / lockfile | None |
| Runnable services | None |
| Lint / test / build | N/A |

### After

| Item | Status |
|------|--------|
| Monorepo | pnpm workspaces (`apps/api`, `apps/web`, `packages/shared`) |
| API | Express on port **3001** (in-memory incidents) |
| Web | Vite + React on port **5173** |
| Tooling | ESLint, Vitest, TypeScript |
| Docs | `README.md`, `AGENTS.md`, this report |

---

## 3. Services

| Service | Required | Port | How to start |
|---------|----------|------|----------------|
| `@emanaguard/api` | MUST | 3001 | `pnpm dev` (repo root) |
| `@emanaguard/web` | MUST | 5173 | `pnpm dev` (repo root) |
| `@emanaguard/shared` | MUST (build) | — | Built once at start of `pnpm dev` / `pnpm test` |

**Note:** Run `pnpm dev` from the repo root so both API and web start. Web alone will fail to load incidents.

---

## 4. Environment variables

| Variable | Required | Default | Notes |
|----------|----------|---------|--------|
| `PORT` | No | `3001` | API listen port |

No secrets required for local or Cloud Agent dev.

---

## 5. VM update script

Registered for Cloud Agent session startup:

```bash
pnpm install
```

Does **not** start servers, run migrations, or execute tests (per update-script policy).

---

## 6. Commands executed and results

Run from repository root after `pnpm install`:

| Step | Command | Result |
|------|---------|--------|
| Lint | `pnpm lint` | Pass |
| Test | `pnpm test` | Pass (5 tests) |
| Build | `pnpm build` | Pass |
| Dev | `pnpm dev` | API + web healthy |
| Hello world (API) | `POST /api/incidents`, `PATCH` resolve | Pass |
| Hello world (UI) | Create + resolve incident at http://localhost:5173 | Pass |

### Test summary

- `@emanaguard/shared`: 1 test  
- `@emanaguard/api`: 3 tests  
- `@emanaguard/web`: 1 test  

---

## 7. Hello world evidence

**API**

1. `GET /api/health` → `{"ok":true,"service":"emanaguard-api"}`
2. `POST /api/incidents` with title + severity → `201`
3. `PATCH /api/incidents/:id` with `{"status":"resolved"}` → resolved incident

**UI**

1. Open http://localhost:5173  
2. Create incident “Wildfire evacuation zone B” (critical)  
3. Resolve from Active board → status **resolved**

**Artifact:** screen recording saved as `emanaguard-hello-world-demo.mp4` (referenced in PR #1).

---

## 8. Deliverables checklist

| Deliverable | Status |
|-------------|--------|
| Working dev environment (install + run) | Done |
| `AGENTS.md` (Cloud-specific instructions) | Done |
| VM update script (`pnpm install`) | Done |
| `README.md` (human onboarding) | Done |
| Lint / test / build verified | Done |
| Hello world (core product flow) | Done |
| **`PHASE_1_REPORT.md` (this file)** | Done |

---

## 9. Gaps and follow-ups

| Item | Notes |
|------|--------|
| Persistent database | Incidents are in-memory; API restart clears data |
| CI workflow | Not added in this phase |
| `.cursor/environment.json` | Not added; optional for Dockerfile/snapshot workflows |
| `PHASE_N_REPORT.md` naming | This phase is documented as **`PHASE_1_REPORT.md`**. If your playbook uses a different phase index or a single template file name, rename or add `PHASE_<n>_REPORT.md` per your process. |

---

## 10. Instructions for next phase

1. Merge PR #1 (or rebase onto `main`).  
2. Future phases should add their own `PHASE_<n>_REPORT.md` at repo root.  
3. Update `AGENTS.md` when ports, env vars, or startup steps change.
