import json
import re
from collections import Counter
from typing import Any

import httpx

from models import CodeChunk, CodeFile, RepositoryAnalysis, SuggestedIssue
from services.observability_client import send_analysis_trace
from settings import get_settings


STOP_WORDS = {
    "a",
    "about",
    "add",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "code",
    "codebase",
    "do",
    "does",
    "file",
    "files",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "main",
    "of",
    "on",
    "or",
    "repo",
    "repository",
    "should",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "with",
    "would",
}

INTENT_KEYWORDS = {
    "auth": ["auth", "authentication", "authorization", "login", "session", "jwt", "token", "user"],
    "payments": ["payment", "payments", "billing", "stripe", "checkout", "subscription", "invoice"],
    "risks": ["risk", "risks", "issue", "issues", "security", "bug", "debt", "gap"],
    "backend": ["backend", "api", "server", "fastapi", "route", "endpoint", "database", "sqlmodel"],
    "frontend": ["frontend", "ui", "react", "vite", "component", "page", "tsx"],
    "tests": ["test", "tests", "testing", "pytest", "vitest", "jest", "playwright", "coverage"],
    "important": ["important", "entry", "entrypoint", "critical", "core", "modify", "change"],
}


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9_./-]+", text.lower()) if len(token) > 2 and token not in STOP_WORDS]


def _expanded_query_terms(message: str) -> set[str]:
    terms = set(_tokens(message))
    lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in lower or any(keyword in lower for keyword in keywords):
            terms.update(keywords)
    return terms


def _score_text(query_terms: set[str], text: str, path: str = "") -> float:
    if not query_terms:
        return 0.0
    text_tokens = Counter(_tokens(f"{path} {text}"))
    score = 0.0
    path_lower = path.lower()
    text_lower = text.lower()
    for term in query_terms:
        score += text_tokens.get(term, 0)
        if term in path_lower:
            score += 4.0
        if term in text_lower:
            score += 1.0
    return score


def _clip(text: str, limit: int = 900) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    return compact[: limit - 1].rstrip() + "…" if len(compact) > limit else compact


def retrieve_context(analysis: RepositoryAnalysis, message: str, limit: int = 6) -> dict[str, Any]:
    query_terms = _expanded_query_terms(message)
    chunks: list[tuple[float, CodeChunk]] = []
    for chunk in analysis.chunks:
        score = _score_text(query_terms, chunk.redacted_content or chunk.content, chunk.file_path)
        if score > 0:
            chunks.append((score, chunk))
    chunks.sort(key=lambda item: item[0], reverse=True)

    files: list[tuple[float, CodeFile]] = []
    for file in analysis.files:
        score = _score_text(query_terms, file.summary or "", file.path)
        if file.is_entry_point:
            score += 1.5
        if file.is_important:
            score += 1.0
        if score > 0:
            files.append((score, file))
    files.sort(key=lambda item: item[0], reverse=True)

    issues: list[tuple[float, SuggestedIssue]] = []
    for issue in analysis.issues:
        issue_text = f"{issue.title}\n{issue.category}\n{issue.description}\n{issue.evidence}\n{issue.suggested_fix}\n{' '.join(issue.related_files)}"
        score = _score_text(query_terms, issue_text)
        if "risk" in query_terms or "issues" in query_terms:
            score += 2.0
        if score > 0:
            issues.append((score, issue))
    issues.sort(key=lambda item: item[0], reverse=True)

    if not chunks:
        # Demo analyses and shallow scans may have few/no chunks. Use important files as pseudo-retrieval anchors.
        for file in sorted(analysis.files, key=lambda f: (not f.is_entry_point, not f.is_important, f.path))[:limit]:
            score = 1.0 + (1.0 if file.is_entry_point else 0.0) + (0.5 if file.is_important else 0.0)
            files.append((score, file))
        files.sort(key=lambda item: item[0], reverse=True)

    related_files: list[str] = []
    for _, chunk in chunks[:limit]:
        if chunk.file_path not in related_files:
            related_files.append(chunk.file_path)
    for _, file in files[:limit]:
        if file.path not in related_files:
            related_files.append(file.path)
    for _, issue in issues[:3]:
        for path in issue.related_files:
            if path not in related_files:
                related_files.append(path)

    supporting_chunks = [
        {
            "id": chunk.id,
            "file_path": chunk.file_path,
            "language": chunk.language,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "snippet": _clip(chunk.redacted_content or chunk.content, 700),
            "score": round(score, 2),
        }
        for score, chunk in chunks[:limit]
    ]
    if not supporting_chunks:
        for score, file in files[: min(4, limit)]:
            supporting_chunks.append(
                {
                    "id": file.id,
                    "file_path": file.path,
                    "language": file.language,
                    "start_line": 1,
                    "end_line": 1,
                    "snippet": _clip(file.summary or "Important file identified by analysis metadata.", 500),
                    "score": round(score, 2),
                }
            )

    return {
        "query_terms": sorted(query_terms),
        "chunks": chunks[:limit],
        "files": files[:limit],
        "issues": issues[:4],
        "related_files": related_files[:10],
        "supporting_chunks": supporting_chunks,
    }


def _format_files(paths: list[str]) -> str:
    return ", ".join(f"`{path}`" for path in paths) if paths else "the files highlighted in the analysis"


def build_fallback_answer(analysis: RepositoryAnalysis, message: str, context: dict[str, Any]) -> str:
    lower = message.lower()
    related_files = context["related_files"]
    files_text = _format_files(related_files[:5])
    top_issues = [issue for _, issue in context["issues"]]
    top_files = [file for _, file in context["files"]]

    if any(word in lower for word in INTENT_KEYWORDS["auth"]):
        if related_files:
            return (
                f"I found authentication-adjacent signals around {files_text}. Start there and search those modules for login, session, JWT/token, user, or middleware logic. "
                f"If those files do not contain auth code, this analysis suggests auth is either not implemented yet or lives behind external service/config not captured by the static scan."
            )
        return "I did not find strong authentication signals in the persisted chunks. That likely means auth is not implemented in this MVP or was outside the bounded scan. Related files: none confidently identified."

    if any(word in lower for word in INTENT_KEYWORDS["payments"]):
        return (
            f"For payments, modify the API boundary and UI flow first. Based on this analysis, likely starting points are {files_text}. "
            "A pragmatic plan is: add backend checkout/subscription endpoints, add provider config only on the backend, extend shared contracts if present, then add frontend screens/components that call those endpoints."
        )

    if any(word in lower for word in INTENT_KEYWORDS["tests"]):
        issue_hint = top_issues[0].title if top_issues else "critical entry points and API contracts"
        return (
            f"Add tests around {files_text} first. Prioritize smoke coverage for repository intake/API responses, then unit tests for service logic and issue generation. "
            f"The highest-signal testing/risk finding is: {issue_hint}."
        )

    if any(word in lower for word in INTENT_KEYWORDS["risks"]):
        if top_issues:
            issue_lines = "; ".join(f"{issue.severity} {issue.category}: {issue.title}" for issue in top_issues[:3])
            return f"The main risks are {issue_lines}. Related files to inspect first: {files_text}. Overall risk score for this analysis is `{analysis.risk_score}`."
        return f"No high-confidence issues were retrieved for this question. Overall risk score is `{analysis.risk_score}`; inspect {files_text} for the most important code paths."

    if any(word in lower for word in INTENT_KEYWORDS["backend"]):
        return (
            f"Backend architecture: {analysis.architecture_summary or analysis.summary or 'The analysis did not include a detailed architecture summary.'} "
            f"The most relevant backend files from retrieval are {files_text}."
        )

    if "important" in lower or "modify" in lower or "files" in lower:
        if top_files:
            summaries = "; ".join(f"`{file.path}` — {file.summary or 'important analysis file'}" for file in top_files[:4])
            return f"The most important files for this question are {summaries}. Related files: {files_text}."
        return f"Start with {files_text}. These are the strongest file matches from persisted chunks and file metadata."

    return (
        f"Based on the persisted analysis, the best answer is grounded in {files_text}. "
        f"Summary: {analysis.summary or 'No summary is available.'} "
        "Use the related files and supporting snippets below as the evidence trail."
    )


async def generate_ai_chat_answer(analysis: RepositoryAnalysis, message: str, context: dict[str, Any]) -> str | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    chunk_context = [item for item in context["supporting_chunks"][:6]]
    issue_context = [
        {
            "title": issue.title,
            "category": issue.category,
            "severity": issue.severity,
            "description": issue.description,
            "evidence": issue.evidence,
            "related_files": issue.related_files,
        }
        for _, issue in context["issues"][:4]
    ]
    prompt = {
        "question": message,
        "repositoryName": analysis.repository_name,
        "sourceType": analysis.source_type,
        "summary": analysis.summary,
        "architectureSummary": analysis.architecture_summary,
        "detectedStack": analysis.detected_stack,
        "riskScore": analysis.risk_score,
        "relatedFiles": context["related_files"],
        "supportingChunks": chunk_context,
        "issues": issue_context,
        "instructions": "Answer concisely as a senior codebase guide. Always mention related file paths when available. Do not invent secrets or private repository data.",
    }
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "You answer questions about a static repository analysis using only the provided context. Mention uncertainty when evidence is weak."},
            {"role": "user", "content": json.dumps(prompt)},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
    answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return answer or None


async def answer_analysis_chat(analysis: RepositoryAnalysis, message: str) -> dict[str, Any]:
    context = retrieve_context(analysis, message)
    mode = "fallback"
    source = "deterministic"
    answer = build_fallback_answer(analysis, message, context)

    if get_settings().openai_api_key:
        try:
            ai_answer = await generate_ai_chat_answer(analysis, message, context)
            if ai_answer:
                answer = ai_answer
                mode = "ai"
                source = "openai"
        except Exception:
            mode = "ai_fallback"
            source = "deterministic_after_ai_error"

    observability_status = await send_chat_trace(analysis, message, answer, context, mode, source)
    return {
        "answer": answer,
        "related_files": context["related_files"],
        "supporting_chunks": context["supporting_chunks"],
        "mode": mode,
        "source": source,
        "observability_status": observability_status,
    }


async def send_chat_trace(analysis: RepositoryAnalysis, message: str, answer: str, context: dict[str, Any], mode: str, source: str) -> str:
    settings = get_settings()
    trace = await send_analysis_trace(
        {
            "app_name": settings.observability_app_name,
            "session_id": f"{analysis.id}:chat",
            "trace_id": f"{analysis.id}:chat",
            "operation": "ask_codebase",
            "model": settings.openai_model if mode == "ai" else "deterministic-chat",
            "provider": source,
            "status": "success",
            "metadata": {
                "analysis_id": analysis.id,
                "repository_name": analysis.repository_name,
                "mode": mode,
                "related_files": context["related_files"],
                "retrieved_chunks": len(context["supporting_chunks"]),
            },
            "steps": [
                {"step_type": "user_message", "name": "question", "input": _clip(message, 500)},
                {"step_type": "retrieval", "name": "keyword_chunk_retrieval", "output": {"related_files": context["related_files"], "chunks": len(context["supporting_chunks"])}},
                {"step_type": "llm_call" if mode == "ai" else "final_response", "name": "generate_chat_answer", "output": _clip(answer, 900)},
            ],
        }
    )
    return trace.status
