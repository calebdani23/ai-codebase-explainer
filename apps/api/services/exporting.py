from models import RepositoryAnalysis


def _bullet_list(items: list[str], empty: str = "None detected") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def build_markdown_export(analysis: RepositoryAnalysis) -> str:
    important_files = [file for file in analysis.files if file.is_important][:15]
    entry_points = [file for file in analysis.files if file.is_entry_point][:10]
    issue_mode = "AI-assisted" if analysis.observability_status == "sent" and analysis.observability_trace_id else "Static/demo heuristic or AI-fallback"
    lines = [
        f"# Codebase Analysis: {analysis.repository_name}",
        "",
        "## Repository overview",
        f"- Repository URL: {analysis.repository_url or 'n/a'}",
        f"- Branch: {analysis.branch or 'n/a'}",
        f"- Source type: {analysis.source_type}",
        f"- Analysis mode: {analysis.analysis_mode}",
        f"- Status: {analysis.status}",
        f"- Files analyzed: {analysis.files_analyzed} of {analysis.total_files_seen} seen",
        f"- Risk score: {analysis.risk_score}",
        f"- Duration: {analysis.duration_ms or 0} ms",
        f"- Issue generation note: {issue_mode}",
        "",
        "## Executive summary",
        analysis.summary or "No summary available.",
        "",
        "## Architecture summary",
        analysis.architecture_summary or "No architecture summary available.",
        "",
        "## Detected stack",
        _bullet_list(analysis.detected_stack),
        "",
        "## Languages",
        _bullet_list([f"{name}: {count}" for name, count in sorted(analysis.languages.items())]),
        "",
        "## Important files",
        _bullet_list([f"`{file.path}` — {file.summary or file.language}" for file in important_files]),
        "",
        "## Entry points",
        _bullet_list([f"`{file.path}`" for file in entry_points]),
        "",
        "## Suggested issues",
    ]
    if not analysis.issues:
        lines.append("- No suggested issues were stored for this analysis.")
    for index, issue in enumerate(analysis.issues, start=1):
        related = ", ".join(f"`{path}`" for path in issue.related_files) or "No single file identified"
        lines.extend(
            [
                "",
                f"### {index}. {issue.title}",
                f"- Severity: {issue.severity}",
                f"- Priority: {issue.priority}",
                f"- Category: {issue.category}",
                f"- Confidence: {issue.confidence:.2f}",
                f"- Effort: {issue.effort}",
                f"- Related files: {related}",
                "",
                "**Problem**",
                issue.description,
                "",
                "**Evidence**",
                issue.evidence,
                "",
                "**Suggested fix**",
                issue.suggested_fix,
                "",
                "<details>",
                "<summary>GitHub issue Markdown</summary>",
                "",
                "```markdown",
                issue.github_issue_markdown.strip(),
                "```",
                "</details>",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety note",
            "This analysis was produced by static scanning only. Repository code was not executed, dependencies were not installed, and real .env contents are not persisted.",
        ]
    )
    return "\n".join(lines) + "\n"
