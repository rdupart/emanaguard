# AGENTS.md

Guidance for AI agents and developers working in **emanaguard**.

## Repository status

As of the initial commit, this repository contains only `README.md` (project title). There is no application source, package manifest, Docker/Compose configuration, CI workflows, or test suite yet.

When application code is added, update this file with stack-specific commands (install, lint, test, run).

## Cursor Cloud specific instructions

### What runs today

No local services are required. There is nothing to lint, test, build, or run beyond normal Git operations on the repo itself.

### VM tooling (available for future work)

The Cloud Agent VM typically includes:

- **Git** — clone, branch, commit, push
- **Node.js** (via nvm) and **npm** / **pnpm**
- **Python 3.12**

After you add a stack (e.g. `package.json`, `pyproject.toml`, `docker-compose.yml`), document the exact install and dev commands here instead of guessing.

### Suggested workflow once code exists

1. Install dependencies using the repo’s lockfile and package manager (`package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, etc.).
2. Copy or create env files from `.env.example` if the project documents them.
3. Start required services (API, DB, frontend) per README or `docker compose` — not via the VM update script.
4. Run lint and tests before claiming a change is complete.

### Update script scope

The VM **update script** only refreshes dependencies on session start. It must stay minimal (e.g. `npm install`, `pnpm install`). Do not put `docker compose up`, dev servers, migrations, or test commands in the update script.

### Gotchas

- **Empty tree**: Agents should not invent a full app stack; follow manifests and README once they exist.
- **Remote**: `origin` points at `github.com/rdupart/emanaguard`; only `main` exists today.
