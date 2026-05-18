import io
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.parse import urlparse

import httpx
from sqlmodel import Session

from models import CodeChunk, CodeFile, RepositoryAnalysis, SuggestedIssue, now_utc
from services.issue_generation import generate_issues
from services.observability_client import send_analysis_trace
from settings import get_settings


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
    ".cache",
    "vendor",
    "target",
    "bin",
    "obj",
}
IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".svg",
    ".mp4",
    ".mov",
    ".mp3",
    ".wav",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".pdf",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".lock",
}
ALLOWED_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".go",
    ".java",
    ".cs",
    ".php",
    ".rb",
    ".rs",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".prisma",
    ".html",
    ".css",
}
ALLOWED_FILENAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".env.example", "README", "LICENSE"}
ENTRYPOINT_NAMES = {"main.py", "app.py", "manage.py", "server.ts", "server.js", "index.ts", "index.js", "main.tsx", "main.jsx", "App.tsx"}

LANG_BY_EXT = {
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".py": "Python",
    ".go": "Go",
    ".java": "Java",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".sql": "SQL",
    ".prisma": "Prisma",
    ".html": "HTML",
    ".css": "CSS",
}

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)(\s*[:=]\s*)(['\"]?)[^'\"\s]+"), r"\1\2\3[REDACTED]"),
    (re.compile(r"ghp_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED_API_KEY]"),
]


@dataclass
class GitHubRepo:
    owner: str
    repo: str

    @property
    def name(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_public_github_url(repository_url: str) -> GitHubRepo:
    parsed = urlparse(repository_url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("MVP only accepts public https://github.com/<owner>/<repo> URLs")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub URL must include owner and repository name")
    repo = parts[1].removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[0]) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid GitHub owner or repository name")
    return GitHubRepo(owner=parts[0], repo=repo)


def _is_allowed_file(path: Path) -> bool:
    name = path.name
    if name.startswith(".env") and name != ".env.example":
        return False
    return name in ALLOWED_FILENAMES or path.suffix.lower() in ALLOWED_EXTENSIONS


def _language(path: str) -> str:
    pure = PurePosixPath(path)
    if pure.name == "Dockerfile":
        return "Dockerfile"
    return LANG_BY_EXT.get(pure.suffix.lower(), "Text")


def _redact(content: str) -> str:
    redacted = content
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _decode_text(raw: bytes) -> str | None:
    if b"\x00" in raw[:2048]:
        return None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _chunks(content: str, max_lines: int = 80) -> list[tuple[int, int, str]]:
    lines = content.splitlines()
    chunks: list[tuple[int, int, str]] = []
    for start in range(0, len(lines), max_lines):
        selected = lines[start : start + max_lines]
        if not selected:
            continue
        chunks.append((start + 1, start + len(selected), "\n".join(selected)))
    return chunks[:4]


async def _download_repo(repo: GitHubRepo, branch: str | None) -> tuple[bytes, str]:
    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-codebase-explainer"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        meta_url = f"https://api.github.com/repos/{repo.owner}/{repo.repo}"
        meta_response = await client.get(meta_url)
        if meta_response.status_code == 404:
            raise ValueError("Repository not found or not public")
        meta_response.raise_for_status()
        metadata = meta_response.json()
        if metadata.get("private"):
            raise ValueError("Private repositories are not supported in this MVP")
        selected_branch = branch or metadata.get("default_branch") or "main"
        zip_url = f"https://codeload.github.com/{repo.owner}/{repo.repo}/zip/refs/heads/{selected_branch}"
        max_bytes = settings.max_repo_size_mb * 1024 * 1024
        content = bytearray()
        async with client.stream("GET", zip_url) as response:
            if response.status_code == 404 and branch:
                raise ValueError(f"Branch not found: {branch}")
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > max_bytes:
                    raise ValueError(f"Repository download exceeds MAX_REPO_SIZE_MB={settings.max_repo_size_mb}")
        return bytes(content), selected_branch


def _extract_zip_safely(zip_bytes: bytes, destination: Path) -> Path:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        root_name: str | None = None
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("Unsafe archive path detected")
            if root_name is None and member_path.parts:
                root_name = member_path.parts[0]
            archive.extract(member, destination)
    if not root_name:
        raise ValueError("Downloaded repository archive is empty")
    return destination / root_name


def _detect_stack(paths: list[str], contents: dict[str, str]) -> tuple[list[str], dict[str, int]]:
    path_set = set(paths)
    lower_paths = {p.lower() for p in paths}
    languages = Counter(_language(path) for path in paths)
    stack: set[str] = set()

    if any(p.endswith((".ts", ".tsx")) for p in paths):
        stack.add("TypeScript")
    if any(p.endswith((".js", ".jsx")) for p in paths):
        stack.add("JavaScript")
    if any(p.endswith(".py") for p in paths):
        stack.add("Python")
    if any(p.endswith((".html", ".css")) for p in paths):
        stack.add("HTML/CSS")
    if "package.json" in path_set:
        package = contents.get("package.json", "")
        stack.add("Node.js")
        for signal, name in [("react", "React"), ("vite", "Vite"), ("next", "Next.js"), ("tailwind", "Tailwind CSS"), ("express", "Express"), ("fastify", "Fastify"), ("vitest", "Vitest"), ("jest", "Jest")]:
            if signal in package.lower():
                stack.add(name)
    if "requirements.txt" in path_set or "pyproject.toml" in path_set:
        deps = (contents.get("requirements.txt", "") + contents.get("pyproject.toml", "")).lower()
        if "fastapi" in deps or any(p.endswith("main.py") for p in paths):
            stack.add("FastAPI")
        if "django" in deps or "manage.py" in path_set:
            stack.add("Django")
        if "flask" in deps:
            stack.add("Flask")
        if "sqlmodel" in deps or "sqlalchemy" in deps:
            stack.add("SQLAlchemy/SQLModel")
        if "pytest" in deps:
            stack.add("pytest")
    if "vite.config.ts" in path_set or "vite.config.js" in path_set:
        stack.add("Vite")
    if "dockerfile" in lower_paths or any(p.startswith("docker-compose") for p in lower_paths):
        stack.add("Docker")
    if any(p.startswith(".github/workflows/") for p in paths):
        stack.add("GitHub Actions")
    if any(p.endswith(".sql") for p in paths) or any("postgres" in contents.get(p, "").lower() for p in paths):
        stack.add("PostgreSQL/SQL")
    if any(p.endswith("schema.prisma") or p.endswith(".prisma") for p in paths):
        stack.add("Prisma")
    return sorted(stack), dict(languages)


def _important_file(path: str) -> bool:
    name = PurePosixPath(path).name
    return name in ENTRYPOINT_NAMES or name in {"package.json", "requirements.txt", "pyproject.toml", "Dockerfile", "docker-compose.yml", "README.md"} or path.startswith(".github/workflows/")


def _summarize_file(path: str, language: str) -> str:
    name = PurePosixPath(path).name
    if name == "package.json":
        return "Node package manifest; useful for frontend/backend dependency and script detection."
    if name in {"requirements.txt", "pyproject.toml"}:
        return "Python dependency/configuration manifest; useful for backend stack detection."
    if name == "Dockerfile" or name.startswith("docker-compose"):
        return "Container/development infrastructure definition."
    if name == "README.md":
        return "Primary project documentation."
    return f"{language} source/documentation file included in static analysis."


def _risk_score(issues: list[dict[str, object]]) -> str:
    severities = {issue["severity"] for issue in issues}
    if "critical" in severities:
        return "critical"
    if "high" in severities:
        return "high"
    if len(issues) >= 3 or "medium" in severities:
        return "medium"
    return "low"


def _scan_repository(root: Path) -> tuple[list[tuple[str, str, bytes]], int, list[str], list[str], list[str]]:
    settings = get_settings()
    max_file_bytes = settings.max_file_size_kb * 1024
    max_total_bytes = settings.max_repo_size_mb * 1024 * 1024
    total_seen = 0
    total_bytes = 0
    selected: list[tuple[str, str, bytes]] = []
    all_paths: list[str] = []
    oversized_paths: list[str] = []
    real_env_paths: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        rel_path = path.relative_to(root).as_posix()
        all_paths.append(rel_path)
        parts = set(PurePosixPath(rel_path).parts)
        total_seen += 1
        if path.name.startswith(".env") and path.name != ".env.example":
            real_env_paths.append(rel_path)
            continue
        if parts & IGNORED_DIRS or path.suffix.lower() in IGNORED_EXTENSIONS or not _is_allowed_file(path):
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            oversized_paths.append(rel_path)
            continue
        if total_bytes + size > max_total_bytes or len(selected) >= settings.max_files_analyzed:
            continue
        raw = path.read_bytes()
        text = _decode_text(raw)
        if text is None:
            continue
        total_bytes += size
        selected.append((rel_path, text, raw))
    return selected, total_seen, all_paths, oversized_paths, real_env_paths


async def analyze_public_github_repository(
    session: Session,
    repository_url: str,
    branch: str | None = None,
    analysis_mode: str = "quick",
    send_observability: bool = False,
) -> RepositoryAnalysis:
    started = perf_counter()
    repo = parse_public_github_url(repository_url)
    analysis = RepositoryAnalysis(
        repository_url=f"https://github.com/{repo.owner}/{repo.repo}",
        repository_name=repo.name,
        branch=branch,
        source_type="github",
        status="analyzing",
        analysis_mode=analysis_mode,
        observability_status="disabled",
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)

    try:
        zip_bytes, selected_branch = await _download_repo(repo, branch)
        with TemporaryDirectory(prefix="ace_repo_") as tmp:
            root = _extract_zip_safely(zip_bytes, Path(tmp))
            scanned, total_seen, all_paths, oversized_paths, real_env_paths = _scan_repository(root)

        contents = {path: _redact(text) for path, text, _ in scanned}
        paths = [path for path, _, _ in scanned]
        stack, languages = _detect_stack(paths, contents)

        analysis.branch = selected_branch
        analysis.total_files_seen = total_seen
        analysis.files_analyzed = len(scanned)
        analysis.detected_stack = stack
        analysis.languages = languages

        important = [path for path in paths if _important_file(path)][:12]
        analysis.summary = (
            f"Static bounded scan of public GitHub repository {repo.name} on branch {selected_branch}. "
            f"Analyzed {len(scanned)} text-like files out of {total_seen} files seen. "
            f"Detected stack signals: {', '.join(stack) if stack else 'not enough signals detected'}."
        )
        folders = sorted({PurePosixPath(path).parts[0] for path in paths if PurePosixPath(path).parts})[:8]
        analysis.architecture_summary = (
            f"Top-level analyzed areas include {', '.join(folders) if folders else 'root files only'}. "
            f"Important entry/config files include {', '.join(important[:8]) if important else 'none detected in bounded scan'}. "
            "The analysis is static only: no repository code, scripts or dependencies were executed."
        )

        for rel_path, text, raw in scanned:
            language = _language(rel_path)
            code_file = CodeFile(
                analysis_id=analysis.id,
                path=rel_path,
                language=language,
                size_bytes=len(raw),
                is_entry_point=PurePosixPath(rel_path).name in ENTRYPOINT_NAMES,
                is_important=_important_file(rel_path),
                summary=_summarize_file(rel_path, language),
            )
            session.add(code_file)
            session.flush()
            redacted = _redact(text)
            for start_line, end_line, chunk_text in _chunks(redacted):
                session.add(
                    CodeChunk(
                        analysis_id=analysis.id,
                        file_id=code_file.id,
                        file_path=rel_path,
                        language=language,
                        content=chunk_text,
                        redacted_content=chunk_text,
                        start_line=start_line,
                        end_line=end_line,
                        token_estimate=max(1, len(chunk_text) // 4),
                    )
                )

        issue_dicts, issue_mode = await generate_issues(
            repository_name=analysis.repository_name,
            summary=analysis.summary or "",
            architecture_summary=analysis.architecture_summary or "",
            paths=paths,
            total_files_seen=total_seen,
            files_analyzed=len(scanned),
            stack=stack,
            contents=contents,
            all_paths=all_paths,
            oversized_paths=oversized_paths,
            real_env_paths=real_env_paths,
        )
        for issue in issue_dicts:
            session.add(SuggestedIssue(analysis_id=analysis.id, **issue))

        analysis.risk_score = _risk_score(issue_dicts)
        analysis.status = "completed"
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
                    "model": settings.openai_model if issue_mode == "ai" else "deterministic-static-scanner",
                    "provider": "openai" if issue_mode == "ai" else issue_mode,
                    "status": "success",
                    "metadata": {
                        "repository_url": analysis.repository_url,
                        "branch": selected_branch,
                        "files_analyzed": analysis.files_analyzed,
                        "total_files_seen": total_seen,
                        "detected_stack": stack,
                        "issue_mode": issue_mode,
                        "risk_score": analysis.risk_score,
                    },
                    "steps": [
                        {"step_type": "user_message", "name": "repository_analysis_request", "input": {"repository_url": analysis.repository_url, "branch": branch, "analysis_mode": analysis_mode}},
                        {"step_type": "tool_call", "name": "download_github_zip", "output": f"branch={selected_branch}"},
                        {"step_type": "tool_call", "name": "scan_repository", "output": f"{len(scanned)}/{total_seen} files analyzed"},
                        {"step_type": "tool_call", "name": "detect_stack", "output": stack},
                        {"step_type": "llm_call", "name": "generate_architecture_summary", "output": analysis.architecture_summary},
                        {"step_type": "llm_call", "name": "generate_issue_triage", "output": f"Generated {len(issue_dicts)} issues using {issue_mode}"},
                        {"step_type": "final_response", "name": "persist_analysis", "output": analysis.id},
                    ],
                }
            )
            analysis.observability_trace_id = trace.trace_id
            analysis.observability_status = trace.status
            analysis.observability_operations = trace.operations
            analysis.observability_steps = trace.steps
            analysis.observability_error = trace.error

    except Exception as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)
        analysis.summary = f"Repository analysis failed safely: {exc}"
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
                    "model": "deterministic-static-scanner",
                    "provider": "heuristic",
                    "status": "error",
                    "metadata": {"repository_url": analysis.repository_url, "error": str(exc)},
                    "steps": [{"step_type": "error", "name": "analyze_repository", "output": str(exc)}],
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
