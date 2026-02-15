# Engineering — Stack

## Frontend

- **React** + **TypeScript**
- **Vite** — build + dev server with HMR
- Single-page app. No SSR, no Next.js.

## Backend

- **Python**
- **FastAPI** + WebSocket
- Direct everybase integration — Shape introspection, Term evaluation, PV storage access

## Dev

- `make dev` — runs frontend (Vite HMR) and backend (uvicorn --reload) in parallel
- Frontend proxies WebSocket to backend during dev
- Production: backend serves built frontend static files
