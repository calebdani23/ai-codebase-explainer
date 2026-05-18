# Deployment

## GitHub Pages frontend

The web app uses Vite and hash routing. To deploy:

1. Push this repository to GitHub.
2. In Settings > Pages, select GitHub Actions.
3. Set repository variables as needed, especially `VITE_API_URL` for the hosted backend.
4. Run the `Deploy web to GitHub Pages` workflow.

## Render backend

- Root directory: `apps/api`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Environment variables: `DATABASE_URL`, `CORS_ORIGINS`, `OPENAI_API_KEY` optional, `OPENAI_MODEL`, `GITHUB_TOKEN` optional, `OBSERVABILITY_ENABLED`, `OBSERVABILITY_API_URL`, `OBSERVABILITY_INGEST_API_KEY`, `DEMO_MODE`, `PORT`.

## Koyeb backend

Use the same build/start commands and environment variables as Render.

## Database

Future phases should use Neon or Supabase Postgres. Do not rely on local filesystem persistence in production.

## CORS

Set `CORS_ORIGINS` to include local development and the final GitHub Pages origin.
