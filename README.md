# AI Codebase Explainer & Issue Triage

AI-powered engineering assistant for repository understanding, architecture review and issue triage.

## What it solves

This project helps teams quickly understand a software repository, identify its stack and architecture, and convert technical findings into actionable issues. The MVP is designed to work in demo/deterministic mode without an OpenAI key.

## Features planned

- Repository intake for public GitHub URLs and demo repositories.
- Static codebase scanning with safety limits and secret redaction.
- Stack detection, architecture summaries and important file mapping.
- Suggested issue triage with severity, priority, confidence and Markdown export.
- Ask your codebase chat in later phases.
- Optional integration with the AI Agent Observability Dashboard.

## Architecture

- `apps/web`: Vite + React + TypeScript frontend, hash routing and GitHub Pages-ready config.
- `apps/api`: FastAPI backend with `/health`, CORS and Render/Koyeb-ready start command.
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

Run backend:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Check health:

```bash
curl http://localhost:8000/health
```

Run with Docker Compose:

```bash
docker compose up --build
```

Build frontend:

```bash
npm run build:web
```

## Environment variables

Copy `.env.example` to `.env` locally if needed. Do not commit `.env` files or real keys.

Important backend variables: `DATABASE_URL`, `CORS_ORIGINS`, `DEMO_MODE`, `OPENAI_API_KEY` optional, `GITHUB_TOKEN` optional, `OBSERVABILITY_*`, `PORT`.

Important frontend variables: `VITE_API_URL`, `VITE_DEMO_MODE`, `VITE_REPO_URL`, `VITE_OBSERVABILITY_DASHBOARD_URL`.

## Observability story

This project is designed to be instrumented with the prior [AI Agent Observability Dashboard](https://calebdani23.github.io/ai-agent-observability-dashboard/). When enabled in later phases, repository analysis can emit traces for scanning, retrieval, LLM calls, issue triage and errors. The integration is optional and non-blocking.

## Deployment

- Frontend: GitHub Pages via `.github/workflows/deploy-pages.yml`.
- Backend: Render or Koyeb free web service using `apps/api` as root and `uvicorn main:app --host 0.0.0.0 --port $PORT` as the start command.
- Database: future phases should use Neon or Supabase Postgres.

See `docs/deployment.md` for details.

## Screenshots

Screenshots will be added after the UI flows are implemented.

## Roadmap

See `docs/roadmap.md`. Phase 1 establishes the project structure, Vite frontend, FastAPI backend, Docker Compose, health check, CORS, docs and safe environment placeholders.
