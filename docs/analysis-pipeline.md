# Analysis Pipeline

Planned pipeline:

1. Accept a public GitHub URL or demo repository selection.
2. Create an analysis job.
3. Clone or download into a temporary workspace.
4. Enforce repository, file size and file count limits.
5. Scan the file tree and ignore heavy folders such as `.git`, `node_modules`, `dist`, `.venv` and caches.
6. Detect languages and stack heuristically.
7. Extract important files and chunks.
8. Redact possible secrets before prompting or telemetry.
9. Generate deterministic summaries and issues when no AI key is configured.
10. Use AI for enhanced summaries/issues only when configured.
11. Export JSON/Markdown.
12. Send optional, non-blocking observability traces.
