# AGENTS.md

Guidance for AI agents and developers working in **emanaguard**.

## Project overview

pnpm monorepo: shared types, Express API (`apps/api`), Vite React UI (`apps/web`). Incidents are stored in memory (resets on API restart).

## Cursor Cloud specific instructions

### Services (dev)

| Service | Required | Port | Start |
|---------|----------|------|--------|
| API | MUST | 3001 | Included in `pnpm dev` (`@emanaguard/api`) |
| Web | MUST | 5173 | Included in `pnpm dev` (`@emanaguard/web`) |
| Shared (build/watch) | MUST (types) | — | `pnpm dev` builds shared once, then `tsc --watch` |

Start both app processes from the repo root:

```bash
pnpm dev
```

Do not run only the web app without the API — the UI will show a connection error.

### Commands (from repo root)

| Task | Command |
|------|---------|
| Install deps | `pnpm install` |
| Dev servers | `pnpm dev` |
| Lint | `pnpm lint` |
| Test | `pnpm test` |
| Build | `pnpm build` |
| Typecheck | `pnpm typecheck` |

### Environment variables

None required for local dev. Optional: `PORT` on the API (default `3001`).

### Gotchas

- **`@emanaguard/shared` must be built** before API tests or dev import resolved `dist/`. Root `pnpm dev` and `pnpm test` run `pnpm --filter @emanaguard/shared build` first.
- **Web proxy**: Vite proxies `/api` → `http://localhost:3001`; curl the API directly on 3001 for debugging.
- **In-memory data**: Restarting the API clears incidents.

### Update script scope

VM startup should run only `pnpm install` (not `pnpm dev` or Docker).
