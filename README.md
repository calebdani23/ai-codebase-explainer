# AI Codebase Explainer & Issue Triage

AI-powered engineering assistant for repository understanding, architecture review and issue triage.

## What it solves

This project helps teams quickly understand a software repository, identify its stack and architecture, and convert technical findings into actionable issues. The MVP is designed to work in demo/deterministic mode without an OpenAI key.

## Features planned

- Repository intake for public GitHub URLs and demo repositories.
- Static codebase scanning with safety limits and secret redaction.
- Stack detection, architecture summaries and important file mapping.
- Suggested issue triage with severity, priority, confidence, effort, related files and GitHub-ready Markdown.
- Optional AI-assisted issue generation and chat when `OPENAI_API_KEY` is configured; deterministic heuristics remain the fallback.
- Ask your codebase chat by analysis ID with keyword/chunk retrieval, related files and non-blocking observability traces.
- Optional integration with the AI Agent Observability Dashboard.

## Architecture

- `apps/web`: Vite + React + TypeScript frontend, hash routing and GitHub Pages-ready config.
- `apps/api`: FastAPI backend with `/health`, CORS, SQLModel persistence, demo plus public GitHub analysis endpoints and Render/Koyeb-ready start command.
- `packages/shared`: shared TypeScript contracts.
- `packages/observability-client`: optional non-blocking trace client scaffold.
- `examples/demo-repos`: demo inputs for deterministic analysis.
- `docs`: architecture, deployment, issue schema, demo script and observability notes.

## Local commands

Install frontend/workspace dependencies:

```bash
npm install
```

Run frontend:

```bash
npm run dev:web
```

The frontend uses hash routing for GitHub Pages. Main UI routes are:

- `/#/` landing page with value cards and observability story.
- `/#/analyze` repository intake for public GitHub URLs or deterministic demo analysis.
- `/#/analysis/<analysis_id>` professional overview with summary cards, stack, folders, entry points, issues and trace status.
- `/#/analysis/<analysis_id>/architecture` file tree and selected file/folder details.
- `/#/analysis/<analysis_id>/issues` issue triage table and copy-ready Markdown detail view.
- `/#/analysis/<analysis_id>/chat` Phase 6 chat shell backed by existing analysis context.
- `/#/analysis/<analysis_id>/observability` trace status and AI Agent Observability Dashboard integration view.

If the live API is unavailable while demo mode is enabled, the demo intake path can open a deterministic session-local analysis so the product UI remains demoable without secrets or paid services.

Run backend:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

For local development without Postgres, the API defaults to `sqlite:///./local_dev.db` if no `DATABASE_URL` is provided. This is only a developer fallback. Production deployments should set `DATABASE_URL` to Neon, Supabase or another Postgres-compatible database.

Check health:

```bash
curl http://localhost:8000/health
```

Create and inspect a deterministic demo analysis:

```bash
curl -X POST http://localhost:8000/api/demo/analyze \
  -H 'Content-Type: application/json' \
  -d '{"demo_repo":"react-fastapi-saas","analysis_mode":"quick","send_observability":false}'

curl http://localhost:8000/api/analyses
curl http://localhost:8000/api/analyses/<analysis_id>
curl http://localhost:8000/api/analyses/<analysis_id>/issues
curl -X POST http://localhost:8000/api/analyses/<analysis_id>/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What are the main risks in this repo?"}'
curl http://localhost:8000/api/analyses/<analysis_id>/observability
curl http://localhost:8000/api/analyses/<analysis_id>/export.md
curl http://localhost:8000/api/analyses/<analysis_id>/export.json
```

Analyze a small public GitHub repository with the static Phase 3 scanner:

```bash
curl -X POST http://localhost:8000/api/repositories/analyze \
  -H 'Content-Type: application/json' \
  -d '{"repository_url":"https://github.com/octocat/Hello-World","analysis_mode":"quick","send_observability":false}'

curl http://localhost:8000/api/analyses/<analysis_id>
```

The backend downloads a GitHub ZIP archive into a temporary workspace, scans text-like files only, ignores heavy/generated folders, redacts common secret patterns before persistence, creates file/chunk records, and deletes the temporary workspace. It never installs dependencies or executes code from analyzed repositories. Optional `GITHUB_TOKEN` is backend-only and only used for GitHub API rate limits/public access.

Issue triage works without paid services. The backend first builds deterministic findings for documentation gaps, missing tests, missing `.env.example`, API validation signals, oversized files, missing lockfiles, missing CI and committed `.env` paths. If `OPENAI_API_KEY` is set, the backend may ask OpenAI for structured JSON issues, validates/sanitizes the response, and automatically falls back to heuristics if the AI call fails or returns invalid JSON.

Ask Your Codebase works the same way: `POST /api/analyses/<analysis_id>/chat` retrieves relevant persisted chunks, files and suggested issues with deterministic keyword scoring. If `OPENAI_API_KEY` is configured, the backend uses OpenAI with the retrieved context only; if the key is absent or the call fails, it returns a deterministic answer that still includes related files and snippets when possible.

Dedicated export endpoints:

- `GET /api/analyses/<analysis_id>/issues` returns persisted suggested issues.
- `POST /api/analyses/<analysis_id>/chat` answers questions with `answer`, `related_files`, `supporting_chunks`, `mode`, `source` and `observability_status`.
- `GET /api/analyses/<analysis_id>/observability` returns safe trace metadata for the UI: enabled state, send status, trace ID, operations, step summaries and any non-secret delivery error.
- `GET /api/analyses/<analysis_id>/export.md` returns a human-readable Markdown report.
- `GET /api/analyses/<analysis_id>/export.json` returns the structured analysis detail object.

Run with Docker Compose:

```bash
docker compose up --build
```

Build frontend:

```bash
npm run build
# equivalent workspace-specific command:
npm run build:web
```

## Environment variables

Copy `.env.example` to `.env` locally if needed. Do not commit `.env` files or real keys.

Important backend variables: `DATABASE_URL`, `CORS_ORIGINS`, `DEMO_MODE`, `OPENAI_API_KEY` optional for backend-only AI issue triage, `OPENAI_MODEL`, `GITHUB_TOKEN` optional, `MAX_REPO_SIZE_MB`, `MAX_FILE_SIZE_KB`, `MAX_FILES_ANALYZED`, `OBSERVABILITY_*`, `PORT`. `DATABASE_URL` should be Postgres in hosted environments; SQLite is documented only as a local fallback.

Important frontend variables: `VITE_API_URL`, `VITE_DEMO_MODE`, `VITE_REPO_URL`, `VITE_OBSERVABILITY_DASHBOARD_URL`.

Frontend variables are public and compiled into the static bundle. Never expose backend-only secrets such as `OPENAI_API_KEY`, `GITHUB_TOKEN`, `DATABASE_URL` or `OBSERVABILITY_INGEST_API_KEY` with a `VITE_` prefix.

## Observability story

This project is instrumented with the prior [AI Agent Observability Dashboard](https://calebdani23.github.io/ai-agent-observability-dashboard/). Set backend-only variables `OBSERVABILITY_ENABLED=true`, `OBSERVABILITY_API_URL=<dashboard backend URL>`, `OBSERVABILITY_INGEST_API_KEY=<ingest key>` and `OBSERVABILITY_APP_NAME=ai-codebase-explainer` to emit `POST /api/traces` payloads. Analysis traces include `analyze_repository`, stack detection, architecture summary and issue triage steps; chat traces use `ask_codebase` with retrieval and answer-generation steps. Delivery is non-blocking: if the dashboard is down or credentials are invalid, analysis/chat responses still succeed and the UI shows `failed` with safe metadata.

## Deployment

- Frontend: GitHub Pages via `.github/workflows/deploy-pages.yml`. The app uses Vite base `/ai-codebase-explainer/` during Pages builds and hash routing (`/#/...`) to avoid direct-route 404s.
- Backend: Render or Koyeb free web service using `apps/api` as root, `pip install -r requirements.txt` as the build command and `uvicorn main:app --host 0.0.0.0 --port $PORT` as the start command.
- Database: Neon, Supabase or another Postgres-compatible database via backend-only `DATABASE_URL`.
- CORS: set backend `CORS_ORIGINS` to local origins plus the GitHub Pages origin, for example `http://localhost:5173,http://127.0.0.1:5173,https://YOUR_GITHUB_USERNAME.github.io`. Do not include `/ai-codebase-explainer` in CORS origins.

See `docs/deployment.md` for details.

## Screenshots

Screenshots will be added after the UI flows are implemented.

## Roadmap

See `docs/roadmap.md`. Phase 1 establishes the project structure, Vite frontend, FastAPI backend, Docker Compose, health check, CORS, docs and safe environment placeholders.
