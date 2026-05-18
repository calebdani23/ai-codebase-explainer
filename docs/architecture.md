# Architecture

The project is split into a static React frontend, a FastAPI backend, shared TypeScript contracts, an optional observability client, demo repositories and documentation.

- `apps/web`: Vite + React + TypeScript shell prepared for GitHub Pages via hash routing and Vite `base`.
- `apps/api`: FastAPI service prepared for Render/Koyeb style hosting. It owns secrets, CORS, repository analysis and future database access.
- `packages/shared`: Shared TypeScript types for analysis and issue contracts.
- `packages/observability-client`: Non-blocking TypeScript trace client scaffold for `POST /api/traces`.
- `examples/demo-repos`: Deterministic demo inputs for an MVP that works without OpenAI.

The frontend never receives backend secrets. Future analysis jobs will be static: clone/fetch, scan, filter, redact and summarize without executing repository code.
