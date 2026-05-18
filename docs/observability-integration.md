# Observability Integration

This project is designed to connect optionally to the prior AI Agent Observability Dashboard using `POST /api/traces`.

Variables:

- `OBSERVABILITY_ENABLED=false`
- `OBSERVABILITY_API_URL=https://YOUR_OBSERVABILITY_BACKEND_URL`
- `OBSERVABILITY_INGEST_API_KEY=`
- `OBSERVABILITY_APP_NAME=ai-codebase-explainer`

If observability is disabled or the API URL is missing, analysis and UI flows continue normally. If sending fails, clients should log a warning and proceed.

Planned operations include `analyze_repository`, `detect_stack`, `generate_architecture_summary`, `generate_issue_triage` and `ask_codebase` with steps for user messages, tool calls, retrieval, LLM calls, final responses and errors.
