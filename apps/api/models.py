from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def now_utc() -> datetime:
    return datetime.now(UTC)


class RepositoryAnalysis(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id("analysis"), primary_key=True)
    repository_url: str | None = None
    repository_name: str
    branch: str | None = "main"
    source_type: str = "demo"
    status: str = "completed"
    analysis_mode: str = "quick"

    detected_stack: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    languages: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    files_analyzed: int = 0
    total_files_seen: int = 0
    risk_score: str = "medium"
    summary: str | None = None
    architecture_summary: str | None = None
    duration_ms: int | None = None

    observability_trace_id: str | None = None
    observability_status: str = "disabled"
    observability_operations: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    observability_steps: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    observability_error: str | None = None
    error_message: str | None = None

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    files: list["CodeFile"] = Relationship(back_populates="analysis")
    chunks: list["CodeChunk"] = Relationship(back_populates="analysis")
    issues: list["SuggestedIssue"] = Relationship(back_populates="analysis")


class CodeFile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id("file"), primary_key=True)
    analysis_id: str = Field(foreign_key="repositoryanalysis.id", index=True)
    path: str
    language: str
    size_bytes: int = 0
    is_entry_point: bool = False
    is_important: bool = False
    summary: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    analysis: RepositoryAnalysis = Relationship(back_populates="files")
    chunks: list["CodeChunk"] = Relationship(back_populates="file")


class CodeChunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id("chunk"), primary_key=True)
    analysis_id: str = Field(foreign_key="repositoryanalysis.id", index=True)
    file_id: str = Field(foreign_key="codefile.id", index=True)
    file_path: str
    language: str
    content: str
    redacted_content: str
    start_line: int
    end_line: int
    token_estimate: int | None = None
    embedding_id: str | None = None

    analysis: RepositoryAnalysis = Relationship(back_populates="chunks")
    file: CodeFile = Relationship(back_populates="chunks")


class SuggestedIssue(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id("issue"), primary_key=True)
    analysis_id: str = Field(foreign_key="repositoryanalysis.id", index=True)
    title: str
    category: str
    severity: str
    priority: str
    confidence: float
    effort: str
    description: str
    evidence: str
    related_files: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    suggested_fix: str
    github_issue_markdown: str
    created_at: datetime = Field(default_factory=now_utc)

    analysis: RepositoryAnalysis = Relationship(back_populates="issues")
