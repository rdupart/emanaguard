# emanaguard

Emergency incident tracker — a small pnpm monorepo for local development and Cloud Agent demos.

## Stack

| Package | Description | Port (dev) |
|---------|-------------|------------|
| `@emanaguard/shared` | Shared TypeScript types | — |
| `@emanaguard/api` | Express REST API (in-memory store) | **3001** |
| `@emanaguard/web` | Vite + React UI | **5173** |

## Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/) 10+

## Setup

```bash
pnpm install
```

## Commands (repo root)

| Command | Description |
|---------|-------------|
| `pnpm dev` | Build shared types, then start API + web in parallel |
| `pnpm build` | Production build for all packages |
| `pnpm lint` | ESLint across packages |
| `pnpm test` | Vitest unit/API/UI tests |
| `pnpm typecheck` | TypeScript check all packages |

## API

- `GET /api/health` — liveness
- `GET /api/incidents` — list incidents
- `POST /api/incidents` — body: `{ "title": string, "severity": "low"|"medium"|"high"|"critical" }`
- `PATCH /api/incidents/:id` — body: `{ "status": "open"|"resolved" }`

The web app proxies `/api` to `http://localhost:3001` during `pnpm dev`.

## Hello world

1. `pnpm dev`
2. Open http://localhost:5173
3. Create an incident and click **Resolve**
