# Engineering — Stack

## Frontend

- **React** + **TypeScript** (strict mode)
- **Vite** — build + dev server with HMR
- **Tailwind CSS** — utility-first styling
- **shadcn/ui** — component primitives (Radix UI + Tailwind, copy-paste, full control)
- **Biome** — lint + format (single tool, replaces ESLint + Prettier)
- Single-page app. No SSR, no Next.js.
- `package-lock.json` committed

## Backend

- **Python ≥ 3.10**
- **FastAPI** + WebSocket
- **Ruff** — lint + format
- Direct everybase integration — Shape introspection, Term evaluation, PV storage access
- `uv.lock` committed

## Stores

- **Schema store** — global, fetched once on connect, immutable. The full Shape tree. Drives component selection and navigation. React context.
- **Data** — component-local via hooks. Each component evaluates a Term, holds the result, renders it. Navigate away — it's gone. No global data cache, no external state library.

## Dependency Policy

The pip package ships a pre-built frontend bundle — no JS runtime needed at install time. This means:

- **Frontend** — pin to latest versions aggressively. The bundle is frozen at build time, so there's zero compatibility surface. Always use the newest React, Tailwind, Vite, etc.
- **Backend** — keep Python deps loose (`>=` floors, no upper bounds). Users install everylens into their own environments alongside everybase and other packages. Tight pins cause resolver conflicts.

## Dev

- `make dev` — runs frontend (Vite HMR) and backend (uvicorn --reload) in parallel
- Frontend proxies WebSocket to backend during dev
- Production: backend serves built frontend static files

## CI

- Lint + typecheck + test on every push
- Frontend: `tsc --noEmit`, Biome, Vitest
- Backend: Ruff, pytest
