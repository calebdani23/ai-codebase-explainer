import json
import re
from pathlib import PurePosixPath
from typing import Any

import httpx

from settings import get_settings


ALLOWED_CATEGORIES = {"bug", "security", "performance", "refactor", "testing", "docs", "architecture", "maintainability"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_PRIORITIES = {"p1", "p2", "p3", "p4"}
ALLOWED_EFFORTS = {"small", "medium", "large"}


def issue_markdown(title: str, description: str, evidence: str, fix: str, related_files: list[str]) -> str:
    files = "\n".join(f"- `{path}`" for path in related_files) or "- No single file identified"
    return (
        f"# {title}\n\n"
        f"## Problem\n{description}\n\n"
        f"## Evidence\n{evidence}\n\n"
        f"## Related files\n{files}\n\n"
        f"## Suggested fix\n{fix}\n"
    )


def _clean_text(value: Any, fallback: str, max_len: int = 1200) -> str:
    text = str(value or fallback).strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_len] or fallback


def _priority_for_severity(severity: str) -> str:
    return {"critical": "p1", "high": "p1", "medium": "p2", "low": "p3"}.get(severity, "p3")


def normalize_issue(raw: dict[str, Any], known_paths: set[str]) -> dict[str, object] | None:
    title = _clean_text(raw.get("title"), "Review repository risk", 160)
    description = _clean_text(raw.get("description"), "A repository improvement opportunity was detected.")
    evidence = _clean_text(raw.get("evidence"), "Detected during static repository analysis.")
    suggested_fix = _clean_text(raw.get("suggestedFix") or raw.get("suggested_fix"), "Review and address this finding.")

    category = str(raw.get("category") or "maintainability").lower().strip()
    if category not in ALLOWED_CATEGORIES:
        category = "maintainability"
    severity = str(raw.get("severity") or "medium").lower().strip()
    if severity not in ALLOWED_SEVERITIES:
        severity = "medium"
    priority = str(raw.get("priority") or _priority_for_severity(severity)).lower().strip()
    if priority not in ALLOWED_PRIORITIES:
        priority = _priority_for_severity(severity)
    effort = str(raw.get("effort") or "medium").lower().strip()
    if effort not in ALLOWED_EFFORTS:
        effort = "medium"
    try:
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.7))))
    except (TypeError, ValueError):
        confidence = 0.7

    related_raw = raw.get("relatedFiles") or raw.get("related_files") or []
    if not isinstance(related_raw, list):
        related_raw = []
    related_files = []
    for item in related_raw:
        path = str(item).strip().lstrip("/")
        if path and (not known_paths or path in known_paths) and path not in related_files:
            related_files.append(path)
    related_files = related_files[:8]

    markdown = raw.get("githubIssueMarkdown") or raw.get("github_issue_markdown")
    markdown = _clean_text(markdown, issue_markdown(title, description, evidence, suggested_fix, related_files), 5000)
    if "## Problem" not in markdown or "## Suggested fix" not in markdown:
        markdown = issue_markdown(title, description, evidence, suggested_fix, related_files)

    return {
        "title": title,
        "category": category,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "effort": effort,
        "description": description,
        "evidence": evidence,
        "related_files": related_files,
        "suggested_fix": suggested_fix,
        "github_issue_markdown": markdown,
    }


def validate_issue_payload(payload: Any, known_paths: set[str]) -> list[dict[str, object]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("issues"), list):
        return []
    issues: list[dict[str, object]] = []
    seen_titles: set[str] = set()
    for raw in payload["issues"]:
        if not isinstance(raw, dict):
            continue
        issue = normalize_issue(raw, known_paths)
        if not issue or issue["title"] in seen_titles:
            continue
        seen_titles.add(str(issue["title"]))
        issues.append(issue)
    return issues[:8]


def build_heuristic_issues(
    paths: list[str],
    total_files_seen: int,
    files_analyzed: int,
    stack: list[str],
    contents: dict[str, str] | None = None,
    all_paths: list[str] | None = None,
    oversized_paths: list[str] | None = None,
    real_env_paths: list[str] | None = None,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    contents = contents or {}
    all_paths = all_paths or paths
    oversized_paths = oversized_paths or []
    real_env_paths = real_env_paths or []
    lower = {p.lower() for p in paths}
    all_lower = {p.lower() for p in all_paths}
    known_paths = set(paths)

    def add(title: str, category: str, severity: str, priority: str, confidence: float, effort: str, description: str, evidence: str, related: list[str], fix: str) -> None:
        raw = {
            "title": title,
            "category": category,
            "severity": severity,
            "priority": priority,
            "confidence": confidence,
            "effort": effort,
            "description": description,
            "evidence": evidence,
            "related_files": [p for p in related if p in known_paths],
            "suggested_fix": fix,
        }
        issue = normalize_issue(raw, known_paths)
        if issue and issue["title"] not in {existing["title"] for existing in issues}:
            issues.append(issue)

    readme_paths = [p for p in paths if PurePosixPath(p).name.lower() == "readme.md"]
    readme_text = "\n".join(contents.get(p, "") for p in readme_paths)
    if not readme_paths or len(readme_text.strip()) < 500:
        add(
            "Improve README with setup, architecture and operational notes" if readme_paths else "Add a README with setup and architecture notes",
            "docs", "medium", "p2", 0.86 if not readme_paths else 0.78, "small",
            "The repository README is missing or too thin for a new engineer to run and understand the system quickly.",
            "README.md was not found or contains fewer than 500 characters in the bounded scan.",
            readme_paths,
            "Document project purpose, local commands, environment variables, architecture boundaries and deployment steps.",
        )
    if ".env.example" not in lower:
        add("Provide a safe .env.example for local setup", "docs", "medium", "p2", 0.82, "small", "No safe environment template was found, which makes local onboarding and secret handling unclear.", ".env.example was not detected; real .env files are ignored and never persisted.", [], "Add .env.example with placeholder values only and document backend-only secrets.")
    if real_env_paths:
        add("Remove real environment files from the repository", "security", "critical", "p1", 0.96, "small", "A real .env-style file path was detected. The scanner did not persist its contents, but the file should not be committed.", f"Detected environment file path(s): {', '.join(real_env_paths[:5])}. Contents were not stored.", [], "Remove committed .env files, rotate any exposed credentials, and keep only .env.example placeholders.")
    if not any("test" in p or "spec" in p or p.endswith("pytest.ini") or "vitest" in p or "jest" in p or "playwright" in p for p in all_lower):
        add("Add automated tests for critical paths", "testing", "medium", "p2", 0.80, "medium", "No obvious test files or test configuration were detected.", "Filenames did not include common test/spec or pytest/vitest/jest/playwright signals.", [], "Start with smoke tests for main entry points, API contracts and highest-risk business logic.")
    api_files = [p for p in paths if p.endswith((".py", ".ts", ".js")) and any(token in p.lower() for token in ("api", "route", "controller", "main.py", "server"))]
    combined_api = "\n".join(contents.get(p, "")[:4000].lower() for p in api_files[:10])
    if api_files and not any(signal in combined_api for signal in ("basemodel", "pydantic", "zod", "joi", "yup", "schema", "validator", "validate")):
        add("Add explicit request validation around API entry points", "security", "high", "p1", 0.72, "medium", "API-looking files were detected without strong validation signals in the sampled content.", "No common validation markers such as Pydantic, Zod, Joi, schema or validate were found near API entry points.", api_files[:5], "Validate request bodies, query params and path params before they reach service or persistence layers.")
    large_related = [p for p in oversized_paths if p in known_paths]
    if oversized_paths:
        add("Review very large files for maintainability", "maintainability", "medium", "p2", 0.73, "medium", "One or more files exceeded the configured scanner file-size limit and may hide complexity from review.", f"Oversized file paths detected: {', '.join(oversized_paths[:8])}.", large_related, "Split large source files by responsibility or document why large generated/config files are expected.")
    names = [PurePosixPath(p).name.lower() for p in paths]
    duplicated_names = sorted({name for name in names if names.count(name) >= 3 and name not in {"index.ts", "index.js", "__init__.py"}})
    if duplicated_names:
        related = [p for p in paths if PurePosixPath(p).name.lower() in duplicated_names[:3]][:8]
        add("Review repeated module names for duplication", "refactor", "low", "p3", 0.66, "medium", "Several repeated filenames may indicate copy/pasted modules or unclear boundaries.", f"Repeated filenames include: {', '.join(duplicated_names[:5])}.", related, "Compare repeated modules, extract shared helpers where useful, and clarify naming for distinct responsibilities.")
    if "Docker" not in stack and not any("deploy" in p or "render.yaml" in p or "fly.toml" in p or "vercel.json" in p for p in all_lower):
        add("Document or add a reproducible deployment workflow", "architecture", "low", "p3", 0.69, "small", "No Dockerfile or deployment-oriented files were detected in this bounded scan.", "Docker/deployment signals were absent from detected stack.", [], "Add Dockerfile, deploy docs, or platform-specific config once runtime is finalized.")
    has_package = "package.json" in lower
    has_lockfile = any(p.endswith(("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb")) for p in all_lower)
    if has_package and not has_lockfile:
        add("Commit a JavaScript package lockfile", "maintainability", "medium", "p2", 0.76, "small", "A package.json was detected without a corresponding lockfile, which can make installs non-reproducible.", "No npm, pnpm, yarn or bun lockfile path was seen.", [p for p in paths if p.lower() == "package.json"], "Generate and commit the lockfile for the selected package manager.")
    if not any(p.startswith(".github/workflows/") for p in all_paths):
        add("Add CI for build and test confidence", "maintainability", "low", "p3", 0.72, "small", "No GitHub Actions workflows were detected.", "No files under .github/workflows/ were analyzed.", [], "Add a simple CI workflow that installs dependencies and runs tests/builds.")
    if total_files_seen > files_analyzed:
        add("Review skipped files against scanner limits", "maintainability", "low", "p4", 0.65, "small", "Some files were skipped by safety filters or limits; ensure critical source files are within bounds.", f"Seen {total_files_seen} files, analyzed {files_analyzed} files.", [], "Tune file size/count limits or document intentionally ignored generated assets.")
    if not issues:
        add("Perform a deeper architecture and quality review", "maintainability", "low", "p3", 0.60, "medium", "The bounded heuristic scan found no major gaps, but a deeper review should validate runtime behavior and tests.", "Baseline issue generated to ensure every analysis has actionable follow-up.", paths[:3], "Run the application test suite, review entry points manually, and add project-specific checks.")
    return issues[:8]


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


async def generate_ai_issues(
    repository_name: str,
    summary: str,
    architecture_summary: str,
    stack: list[str],
    paths: list[str],
    contents: dict[str, str],
) -> list[dict[str, object]]:
    settings = get_settings()
    if not settings.openai_api_key:
        return []

    important_paths = paths[:80]
    snippets = []
    for path in paths[:24]:
        text = contents.get(path, "")[:1200]
        if text:
            snippets.append({"path": path, "sample": text})
    prompt = {
        "repositoryName": repository_name,
        "summary": summary,
        "architectureSummary": architecture_summary,
        "detectedStack": stack,
        "analyzedPaths": important_paths,
        "redactedSamples": snippets,
        "instructions": "Return only JSON with key issues. Each issue must have title, category, severity, priority, confidence, effort, description, evidence, relatedFiles, suggestedFix, githubIssueMarkdown. Do not include secrets.",
    }
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "You are a senior software architecture and security reviewer. Respond only with valid JSON."},
            {"role": "user", "content": json.dumps(prompt)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = _extract_json_object(content)
    return validate_issue_payload(parsed, set(paths)) if parsed else []


async def generate_issues(
    repository_name: str,
    summary: str,
    architecture_summary: str,
    paths: list[str],
    total_files_seen: int,
    files_analyzed: int,
    stack: list[str],
    contents: dict[str, str] | None = None,
    all_paths: list[str] | None = None,
    oversized_paths: list[str] | None = None,
    real_env_paths: list[str] | None = None,
) -> tuple[list[dict[str, object]], str]:
    contents = contents or {}
    heuristic = build_heuristic_issues(paths, total_files_seen, files_analyzed, stack, contents, all_paths, oversized_paths, real_env_paths)
    if not get_settings().openai_api_key:
        return heuristic, "heuristic"
    try:
        ai_issues = await generate_ai_issues(repository_name, summary, architecture_summary, stack, paths, contents)
        if ai_issues:
            return ai_issues, "ai"
    except Exception:
        pass
    return heuristic, "ai_fallback"
