# Analysis Pipeline

Implemented MVP pipeline:

1. Accept a public GitHub URL or demo repository selection.
2. Create an analysis job.
3. Download a GitHub ZIP archive into a temporary workspace. No analyzed repository code is executed and no dependencies are installed.
4. Enforce repository, file size and file count limits.
5. Scan the file tree and ignore heavy folders such as `.git`, `node_modules`, `dist`, `.venv` and caches.
6. Detect languages and stack heuristically.
7. Extract important files and persist bounded chunks for later retrieval.
8. Redact possible secrets before persistence, prompting or telemetry. Real `.env` files are ignored; `.env.example` is allowed.
9. Generate deterministic summaries and heuristic issues when no AI key is configured.
10. If `OPENAI_API_KEY` exists, request structured JSON issue triage from OpenAI, validate/sanitize it, and fall back to heuristics on any failure.
11. Persist GitHub-ready issue Markdown and expose JSON/Markdown exports.
12. Serve Ask Your Codebase requests by retrieving relevant persisted chunks, important files and issues by keyword scoring.
13. If `OPENAI_API_KEY` exists, answer chat with OpenAI using only the bounded retrieved context; otherwise, or if the provider call fails, synthesize a deterministic fallback answer.
14. Send optional, non-blocking observability traces.

## Safety limits

The public repository scanner is intentionally bounded for free-tier hosting and portfolio demos:

- `MAX_REPO_SIZE_MB` caps the downloaded ZIP and total scanned bytes.
- `MAX_FILE_SIZE_KB` skips individual large files.
- `MAX_FILES_ANALYZED` caps persisted analyzed files.
- Heavy folders such as `.git`, `node_modules`, `dist`, `build`, `.next`, `.venv`, caches, coverage and `vendor` are ignored.
- Binary/media/archive/font/executable files are skipped.
- Only text-like source/config/docs extensions and known filenames such as `Dockerfile` and `.env.example` are analyzed.

## Stack detection

Detection is heuristic and deterministic. It checks manifests and filenames for common signals: `package.json`, Vite/React/Next/Tailwind dependencies, Python manifests, FastAPI/Django/Flask/SQLModel/pytest dependencies, Docker files, `.github/workflows`, SQL/Prisma files and common TypeScript/JavaScript/Python source extensions.

## Issue triage and exports

Every completed analysis stores at least one `SuggestedIssue`. Heuristics cover missing or thin README files, missing `.env.example`, committed `.env` paths without storing contents, missing tests, weak API validation signals, oversized files, repeated filenames, missing deployment/CI signals and package manifests without lockfiles. AI-assisted triage is backend-only and optional: invalid JSON, schema violations or API errors automatically use the heuristic output.

Export endpoints:

- `GET /api/analyses/{analysis_id}/issues`
- `GET /api/analyses/{analysis_id}/export.md`
- `GET /api/analyses/{analysis_id}/export.json`

## Ask Your Codebase retrieval

The Phase 6 chat endpoint is intentionally simple and explainable. `POST /api/analyses/{analysis_id}/chat` expands the user question with common engineering intents such as auth, payments, risks, backend, frontend and tests. It scores persisted chunks, file summaries and suggested issues by keyword/path matches, then returns an answer plus `related_files` and `supporting_chunks`. This keeps the MVP free-hosting friendly and avoids embeddings/vector infrastructure until a later phase.
