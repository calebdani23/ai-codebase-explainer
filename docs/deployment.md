# Deployment

Phase 8 deployment targets are intentionally free-hosting friendly:

- Static frontend on GitHub Pages.
- FastAPI backend on Render Free Web Service or Koyeb Free Web Service.
- External Postgres on Neon, Supabase or another Postgres-compatible provider.

The frontend must never contain secrets. Only `VITE_*` public values are compiled into the GitHub Pages bundle.

## 1. GitHub Pages frontend

The web app is a Vite + React static build in `apps/web`. It uses `HashRouter`, so routes such as `/#/analysis/<id>` work on GitHub Pages without server-side rewrites.

Vite uses this repo-page base path when the workflow sets `GITHUB_PAGES=true`:

```ts
base: '/ai-codebase-explainer/'
```

Deploy steps:

1. Push this repository to GitHub.
2. In GitHub, open **Settings > Pages**.
3. Set **Build and deployment > Source** to **GitHub Actions**.
4. Add repository variable `VITE_API_URL` with the hosted API origin, for example `https://ai-codebase-explainer-api.onrender.com`.
5. Run or push to trigger `.github/workflows/deploy-pages.yml`.

The workflow runs from the repository root, installs workspace dependencies with `npm ci`, builds with `GITHUB_PAGES=true npm run build`, and uploads `apps/web/dist`.

Useful public frontend variables:

| Variable | Purpose | Secret? |
| --- | --- | --- |
| `VITE_API_URL` | Public HTTPS URL of the hosted backend. | No |
| `VITE_DEMO_MODE` | Keeps deterministic demo fallback available. | No |
| `VITE_REPO_URL` | Link to this GitHub repository. | No |
| `VITE_OBSERVABILITY_DASHBOARD_URL` | Public dashboard UI link. | No |

Do not add `OPENAI_API_KEY`, `GITHUB_TOKEN`, database URLs or ingest keys as frontend variables.

## 2. Render backend

Create a **Render Web Service**:

- Root directory: `apps/api`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Render injects `PORT`; the start command must use `$PORT`, not a hard-coded port.

This repo also includes `render.yaml` as a lightweight blueprint. It documents the same build/start commands and marks secret values with `sync: false` so real credentials are entered in Render, not committed.

## 3. Koyeb backend

Create a Koyeb Web Service from the repository:

- Service type: Web Service
- Root directory / working directory: `apps/api`
- Build command: `pip install -r requirements.txt`
- Run command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `GET /health`

Koyeb also provides the `PORT` environment variable. Keep the same backend environment variables listed below.

## 4. Database: Neon, Supabase or Postgres

Hosted environments should use external Postgres:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Notes:

- Neon and Supabase connection strings are both Postgres-compatible.
- Common `postgres://` and `postgresql://` URLs are normalized for the psycopg driver by the API database layer.
- SQLite is a developer fallback only. Do not rely on local filesystem persistence in Render/Koyeb because instances can restart or be replaced.
- Temporary repository ZIP extraction is safe to perform on ephemeral disk because analysis results are persisted to the database.

## 5. Backend environment variables

Minimum hosted backend setup:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://YOUR_GITHUB_USERNAME.github.io
DEMO_MODE=true
OPENAI_MODEL=gpt-4o-mini
MAX_REPO_SIZE_MB=25
MAX_FILE_SIZE_KB=300
MAX_FILES_ANALYZED=300
OBSERVABILITY_ENABLED=false
OBSERVABILITY_APP_NAME=ai-codebase-explainer
```

Optional backend-only variables:

```env
OPENAI_API_KEY=...
GITHUB_TOKEN=...
OBSERVABILITY_API_URL=https://YOUR_OBSERVABILITY_BACKEND_URL
OBSERVABILITY_INGEST_API_KEY=...
```

Backend-only means these values are set only in Render/Koyeb. They must not be committed and must not be prefixed with `VITE_`.

## 6. CORS

`CORS_ORIGINS` is a comma-separated list of origins allowed to call the API from browsers.

Examples:

```env
# Local development only
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Local + GitHub Pages
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://calebdani23.github.io
```

Important: CORS origins are only `scheme://host[:port]`. Do not include paths such as `/ai-codebase-explainer`; the browser sends the origin as `https://calebdani23.github.io` even when the app is served from `https://calebdani23.github.io/ai-codebase-explainer/`.

## 7. Verification checklist

Run locally before deployment:

```bash
npm ci
npm run build
```

Backend start command smoke test:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export PORT=8000
uvicorn main:app --host 0.0.0.0 --port $PORT
curl http://localhost:8000/health
```

After deployment:

1. Open the GitHub Pages URL and confirm the landing page loads.
2. Confirm hash routes refresh correctly, for example `/#/analyze`.
3. Open the backend `/health` URL.
4. In the frontend, run a deterministic demo analysis.
5. If browser requests fail, verify `VITE_API_URL` points to the backend and `CORS_ORIGINS` includes `https://YOUR_GITHUB_USERNAME.github.io`.

## 8. Troubleshooting

- **Blank or broken assets on Pages**: confirm the workflow used `GITHUB_PAGES=true npm run build` and Vite emitted assets under `/ai-codebase-explainer/`.
- **404 on nested frontend routes**: use hash URLs (`/#/...`); the app is intentionally configured with `HashRouter`.
- **CORS error**: add the GitHub Pages origin only, not the repository path, to `CORS_ORIGINS`.
- **Backend fails to boot on Render/Koyeb**: verify `DATABASE_URL` is reachable and the start command uses `$PORT`.
- **Demo works but AI does not**: `OPENAI_API_KEY` is optional; set it only on the backend service if AI-assisted summaries/issues/chat are desired.
