# Issue Schema

`SuggestedIssue` captures actionable engineering findings:

- `title`: concise problem statement.
- `category`: `bug`, `security`, `performance`, `refactor`, `testing`, `docs`, `architecture` or `maintainability`.
- `severity`: `low`, `medium`, `high` or `critical`.
- `priority`: `p1` through `p4`.
- `confidence`: numeric confidence from `0` to `1`.
- `effort`: `small`, `medium` or `large`.
- `description`, `evidence`, `relatedFiles`, `suggestedFix`.
- `githubIssueMarkdown`: ready-to-copy Markdown for GitHub Issues.

## Generation modes

The backend always supports deterministic heuristic issue triage. When `OPENAI_API_KEY` is present, the API can request structured JSON in this shape:

```json
{
  "issues": [
    {
      "title": "Missing input validation in API route",
      "category": "security",
      "severity": "high",
      "priority": "p1",
      "confidence": 0.86,
      "effort": "medium",
      "description": "The API route accepts user input without schema validation.",
      "evidence": "Request body is passed directly into service layer.",
      "relatedFiles": ["apps/api/routes/users.py"],
      "suggestedFix": "Add request schema validation and reject malformed input.",
      "githubIssueMarkdown": "# Missing input validation in API route\n\n## Problem\n..."
    }
  ]
}
```

AI output is sanitized before persistence: enum values are normalized, confidence is clamped to `0..1`, related files must match analyzed paths, text is length-limited and GitHub Markdown is regenerated if required sections are missing. If validation fails, heuristic issues are saved instead.

## Export/copy support

- `GET /api/analyses/{analysis_id}/issues` returns issue records for UI copy buttons.
- `GET /api/analyses/{analysis_id}/export.md` returns a portfolio-quality Markdown report with issue Markdown blocks.
- `GET /api/analyses/{analysis_id}/export.json` returns the structured analysis detail object.
