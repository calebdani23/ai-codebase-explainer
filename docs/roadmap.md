# Roadmap

## Current MVP status

The portfolio MVP now covers the intended phases:

- ✅ Base project structure, Vite frontend, FastAPI backend, Docker Compose and environment examples.
- ✅ Demo analysis path that works without paid AI services.
- ✅ Public GitHub static scanner with safety filters, limits and redaction.
- ✅ Heuristic and optional AI-assisted issue triage with Markdown/JSON exports.
- ✅ Product UI for landing, intake, overview, architecture, issues, chat and observability.
- ✅ Ask Your Codebase with deterministic fallback and related files/snippets.
- ✅ Optional non-blocking integration with the prior AI Agent Observability Dashboard.
- ✅ Deployment documentation for GitHub Pages, Render/Koyeb and Neon/Supabase.
- ✅ Portfolio polish, demo script and screenshot placeholders.

## Near-term improvements

1. **Replace placeholders with real screenshots** after the public frontend/backend are deployed.
2. **Add smoke tests** for demo analysis, routing and issue-copy interactions.
3. **Improve scanner explainability** by showing ignored file counts by reason in the UI/export.
4. **Add background job status** for larger repositories instead of request/response-only analysis.
5. **Expand demo repositories** to include a Node API, Python service and monorepo example.

## Product extensions

- GitHub issue creation behind explicit user confirmation and OAuth, not in the MVP.
- Semantic retrieval with embeddings/pgvector for better Ask Your Codebase answers.
- Team-ready saved analyses, comparison between commits/branches and trend views.
- Rule configuration for organization-specific risk policies.
- Rich trace deep links into the AI Agent Observability Dashboard when the dashboard deployment exposes stable trace URLs.

## Engineering hardening

- Add backend unit tests around scanner limits, redaction and issue generation fallback.
- Add frontend component/route tests for empty, loading, failed and demo states.
- Add rate limiting and queueing before allowing broad public use.
- Add schema migrations if the data model evolves beyond SQLModel auto-create for MVP usage.
- Add structured logging and deployment dashboards for the API service itself.
