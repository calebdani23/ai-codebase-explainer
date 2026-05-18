# Demo Script

Use this as a 5-7 minute recruiter/client walkthrough. The goal is to show that this is a practical AI engineering product with safe fallbacks, not just a chat UI.

## Pre-demo checklist

- Frontend is available locally or on GitHub Pages.
- Backend is running if you want live API calls; otherwise keep `VITE_DEMO_MODE=true` so the frontend demo fallback remains available.
- No secrets are shown in the browser. Backend-only keys stay in server environment variables.
- Optional: observability backend variables are configured if you want to show a `sent` trace. If not, explain the disabled/failed status honestly.

## Talk track

1. **Landing page — product framing**
   - Open `/#/`.
   - Say: “This turns a public repository into an engineering brief: stack, architecture, risks, suggested issues, exports and chat.”
   - Point out the safety posture: public repos, static scan, no frontend secrets, deterministic fallback.

2. **Portfolio story — observability-first AI**
   - Explain: “First I built the AI Agent Observability Dashboard. Then I built this repository-analysis product and instrumented it with that dashboard.”
   - Open the dashboard link only briefly; return to this product.

3. **Repository intake**
   - Click **Try Demo Repository**.
   - Keep **Use demo repository** checked and choose **Quick Scan**.
   - Mention that a real public GitHub URL can be submitted, but private repos/secrets are intentionally out of scope for the MVP.
   - Start analysis.

4. **Analysis overview**
   - Show repository name, files analyzed, stack, language mix, risk score, suggested issue count, duration and trace status.
   - Read the executive summary and architecture summary as the “under 2 minutes” value proposition.

5. **Architecture explorer**
   - Open **Architecture**.
   - Click a key file/folder and show purpose, importance, size and recommendations.
   - Explain that this helps a new engineer decide what to read first.

6. **Issue triage**
   - Open **Issues**.
   - Select a high-value issue and show severity, priority, category, confidence, effort, evidence, related files and suggested fix.
   - Click **Copy Markdown** and explain that the MVP does not create real GitHub issues; it produces reviewable drafts.

7. **Ask Your Codebase**
   - Open **Ask your codebase**.
   - Ask: “What are the main risks in this repo?” or “Which tests should be added first?”
   - Point out related files and supporting snippets. Mention OpenAI is optional; deterministic answers keep the product demoable.

8. **Observability view**
   - Open **Observability**.
   - Explain operations represented: scan, stack detection, architecture summary, issue triage and chat.
   - If status is `sent`, describe how the trace would appear in the AI Agent Observability Dashboard. If disabled/failed, emphasize non-blocking delivery and safe metadata.

9. **Exports and engineering judgment**
   - Open `/api/analyses/<analysis_id>/export.md` or use the JSON endpoint if the backend is running.
   - Close by naming the engineering choices: safe static scanning, backend-owned secrets, Postgres-ready persistence, deployable free-tier architecture and observability integration.

## Backup path

If the backend is unavailable during a presentation, use the demo fallback from `/#/analyze?demo=true`. The frontend stores a deterministic local analysis in session storage so overview, architecture, issues, chat and observability screens remain presentable.
