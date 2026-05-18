from pathlib import Path
from time import perf_counter

from sqlmodel import Session

from models import CodeChunk, CodeFile, RepositoryAnalysis, SuggestedIssue, now_utc
from services.issue_generation import generate_issues
from services.observability_client import send_analysis_trace
from settings import get_settings


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "examples" / "demo-repos").exists():
            return parent
    return current.parents[1]


PROJECT_ROOT = _find_project_root()
DEMO_REPOS_DIR = PROJECT_ROOT / "examples" / "demo-repos"


async def create_demo_analysis(
    session: Session,
    demo_repo: str = "react-fastapi-saas",
    analysis_mode: str = "quick",
    send_observability: bool = False,
) -> RepositoryAnalysis:
    started = perf_counter()
    repo_dir = DEMO_REPOS_DIR / demo_repo
    if not repo_dir.exists() and demo_repo != "react-fastapi-saas":
        raise ValueError(f"Unknown demo repository: {demo_repo}")

    readme = repo_dir / "README.md"
    descriptor = readme.read_text(encoding="utf-8") if readme.exists() else "React + FastAPI SaaS deterministic demo repository"

    analysis = RepositoryAnalysis(
        repository_url=f"demo://{demo_repo}",
        repository_name="React + FastAPI SaaS Demo",
        branch="main",
        source_type="demo",
        status="completed",
        analysis_mode=analysis_mode,
        detected_stack=["React", "TypeScript", "Vite", "FastAPI", "Python", "PostgreSQL", "Docker"],
        languages={"TypeScript": 46, "Python": 34, "Markdown": 8, "YAML": 7, "SQL": 5},
        files_analyzed=9,
        total_files_seen=14,
        risk_score="medium",
        summary=(
            "Deterministic demo analysis for a small SaaS-style application with a Vite/React "
            "frontend, FastAPI backend, PostgreSQL persistence and Docker-based local workflow. "
            f"Descriptor: {descriptor.strip()}"
        ),
        architecture_summary=(
            "The system is split into apps/web for the browser UI, apps/api for private backend "
            "logic, packages/shared for contracts, and infrastructure files for deployment. "
            "The backend owns secrets and database access while the frontend consumes JSON APIs."
        ),
    )
    session.add(analysis)
    session.flush()

    files = [
        CodeFile(analysis_id=analysis.id, path="apps/web/src/App.tsx", language="TypeScript", size_bytes=8200, is_entry_point=True, is_important=True, summary="Main React application shell and demo analysis UI entry."),
        CodeFile(analysis_id=analysis.id, path="apps/web/src/api/client.ts", language="TypeScript", size_bytes=2400, is_entry_point=False, is_important=True, summary="Frontend API helper for backend calls."),
        CodeFile(analysis_id=analysis.id, path="apps/api/main.py", language="Python", size_bytes=5600, is_entry_point=True, is_important=True, summary="FastAPI app, CORS, health and analysis endpoints."),
        CodeFile(analysis_id=analysis.id, path="apps/api/services/analysis.py", language="Python", size_bytes=9100, is_entry_point=False, is_important=True, summary="Repository scanning and deterministic analysis pipeline."),
        CodeFile(analysis_id=analysis.id, path="packages/shared/src/index.ts", language="TypeScript", size_bytes=1700, is_entry_point=False, is_important=True, summary="Shared response contracts for web/API alignment."),
        CodeFile(analysis_id=analysis.id, path="docker-compose.yml", language="YAML", size_bytes=1300, is_entry_point=False, is_important=False, summary="Local development orchestration."),
    ]
    session.add_all(files)
    session.flush()

    file_by_path = {file.path: file for file in files}
    chunks = [
        CodeChunk(analysis_id=analysis.id, file_id=file_by_path["apps/api/main.py"].id, file_path="apps/api/main.py", language="Python", content="FastAPI app with CORS, health, demo analysis, repository analysis, analysis detail, issues and export routes. Backend owns secrets and private provider calls.", redacted_content="FastAPI app with CORS, health, demo analysis, repository analysis, analysis detail, issues and export routes. Backend owns secrets and private provider calls.", start_line=1, end_line=80, token_estimate=42),
        CodeChunk(analysis_id=analysis.id, file_id=file_by_path["apps/api/services/analysis.py"].id, file_path="apps/api/services/analysis.py", language="Python", content="Static analysis service downloads public repositories, filters heavy paths, redacts secret-like content, detects stack, creates chunks and suggested issues.", redacted_content="Static analysis service downloads public repositories, filters heavy paths, redacts secret-like content, detects stack, creates chunks and suggested issues.", start_line=1, end_line=140, token_estimate=38),
        CodeChunk(analysis_id=analysis.id, file_id=file_by_path["apps/web/src/App.tsx"].id, file_path="apps/web/src/App.tsx", language="TypeScript", content="React application shell for repository intake, overview, architecture explorer, issue triage, chat shell and observability views.", redacted_content="React application shell for repository intake, overview, architecture explorer, issue triage, chat shell and observability views.", start_line=1, end_line=220, token_estimate=34),
        CodeChunk(analysis_id=analysis.id, file_id=file_by_path["packages/shared/src/index.ts"].id, file_path="packages/shared/src/index.ts", language="TypeScript", content="Shared contracts keep frontend and backend response shapes aligned for analyses, files, chunks and issues.", redacted_content="Shared contracts keep frontend and backend response shapes aligned for analyses, files, chunks and issues.", start_line=1, end_line=80, token_estimate=24),
    ]
    session.add_all(chunks)

    paths = [file.path for file in files]
    contents = {
        "README.md": descriptor,
        "apps/api/main.py": "FastAPI endpoints, Pydantic request models and SQLModel persistence.",
        "apps/web/src/App.tsx": "React UI for analysis overview and issue triage.",
        "apps/api/services/analysis.py": "Static repository analysis, stack detection and issue generation.",
    }
    issue_dicts, issue_mode = await generate_issues(
        repository_name=analysis.repository_name,
        summary=analysis.summary or "",
        architecture_summary=analysis.architecture_summary or "",
        paths=paths,
        total_files_seen=analysis.total_files_seen,
        files_analyzed=analysis.files_analyzed,
        stack=analysis.detected_stack,
        contents=contents,
        all_paths=paths,
    )
    issues = [SuggestedIssue(analysis_id=analysis.id, **issue) for issue in issue_dicts]
    session.add_all(issues)

    analysis.duration_ms = int((perf_counter() - started) * 1000)
    analysis.updated_at = now_utc()

    settings = get_settings()
    if send_observability or settings.observability_enabled:
        trace = await send_analysis_trace(
            {
                "app_name": settings.observability_app_name,
                "session_id": analysis.id,
                "trace_id": analysis.id,
                "operation": "analyze_repository",
                "model": "deterministic-demo",
                "provider": "demo",
                "status": "success",
                "metadata": {
                    "repository_url": analysis.repository_url,
                    "files_analyzed": analysis.files_analyzed,
                    "detected_stack": analysis.detected_stack,
                },
                "steps": [
                    {"step_type": "user_message", "name": "demo_analysis_request", "input": {"demo_repo": demo_repo, "analysis_mode": analysis_mode}},
                    {"step_type": "tool_call", "name": "load_demo_repo", "output": demo_repo},
                    {"step_type": "tool_call", "name": "detect_stack", "output": analysis.detected_stack},
                    {"step_type": "llm_call", "name": "generate_architecture_summary", "output": analysis.architecture_summary},
                    {"step_type": "llm_call", "name": "generate_issue_triage", "output": f"Generated {len(issues)} issues using {issue_mode}"},
                    {"step_type": "final_response", "name": "persist_analysis", "output": analysis.id},
                ],
            }
        )
        analysis.observability_trace_id = trace.trace_id
        analysis.observability_status = trace.status
        analysis.observability_operations = trace.operations
        analysis.observability_steps = trace.steps
        analysis.observability_error = trace.error

    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis
