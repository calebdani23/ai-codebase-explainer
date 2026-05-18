# Observability Integration

This project optionally emits traces to the prior **AI Agent Observability Dashboard** using its `POST /api/traces` ingest contract. The dashboard remains the telemetry backend; this app only stores enough safe metadata to tell the portfolio story in `/analysis/:id/observability`.

## Backend environment

```env
OBSERVABILITY_ENABLED=true
OBSERVABILITY_API_URL=https://YOUR_OBSERVABILITY_BACKEND_URL
OBSERVABILITY_INGEST_API_KEY=replace-with-ingest-key
OBSERVABILITY_APP_NAME=ai-codebase-explainer
```

- `OBSERVABILITY_INGEST_API_KEY` is backend-only. Never create a `VITE_` copy.
- The API appends `/api/traces` to `OBSERVABILITY_API_URL`.
- If `OBSERVABILITY_ENABLED=false` or the API URL is empty, trace status is `disabled` and the app continues normally.
- If the dashboard request fails, the API logs a warning, persists safe status/error metadata, returns the analysis/chat response, and reports status `failed`.

## Frontend environment

```env
VITE_OBSERVABILITY_DASHBOARD_URL=https://calebdani23.github.io/ai-agent-observability-dashboard/
```

This is a public manual dashboard link only. The frontend never receives ingest credentials.

## Operations and steps

Analysis traces use operation `analyze_repository` and include steps representing:

- `user_message` — demo/public repository analysis request metadata.
- `tool_call` — demo load or GitHub ZIP download.
- `tool_call` — bounded static scan.
- `tool_call` — `detect_stack` result.
- `llm_call` — `generate_architecture_summary` (deterministic or AI-assisted summary text).
- `llm_call` — `generate_issue_triage` with issue count and mode (`heuristic`, `ai`, `ai_fallback`, or `demo`).
- `final_response` — persisted analysis ID.
- `error` — safe failure summary when repository analysis fails.

Chat traces use operation `ask_codebase` and include:

- `user_message` — the user's question.
- `retrieval` — related files and supporting chunk count.
- `llm_call` or `final_response` — AI or deterministic answer summary.

## API/UI metadata

`GET /api/analyses/{analysis_id}/observability` returns safe metadata:

```json
{
  "enabled": true,
  "status": "sent",
  "trace_id": "analysis_123",
  "app_name": "ai-codebase-explainer",
  "operations": ["analyze_repository", "detect_stack", "generate_issue_triage"],
  "steps": [{"step_type": "tool_call", "name": "scan_repository", "output": "42/68 files analyzed"}],
  "dashboard_url": "https://YOUR_OBSERVABILITY_BACKEND_URL",
  "error": null
}
```

The frontend observability route displays enabled/disabled state, trace ID, sent/failed/disabled status, operations, step summaries and a manual dashboard link.

## Non-blocking guarantee

The observability client normalizes/clips payloads, removes obvious secret-like metadata keys, uses a short HTTP timeout, and catches all delivery errors. Observability can add status visibility but must never be required for repository analysis, issue triage or chat to succeed.
