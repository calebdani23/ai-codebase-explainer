from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DemoAnalyzeRequest(ApiModel):
    demo_repo: str = "react-fastapi-saas"
    analysis_mode: str = "quick"
    send_observability: bool = False


class CodeFileRead(ApiModel):
    id: str
    path: str
    language: str
    size_bytes: int
    is_entry_point: bool
    is_important: bool
    summary: str | None = None


class CodeChunkRead(ApiModel):
    id: str
    file_id: str
    file_path: str
    language: str
    redacted_content: str
    start_line: int
    end_line: int
    token_estimate: int | None = None


class ChatRequest(ApiModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatSupportingChunk(ApiModel):
    id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    snippet: str
    score: float


class ChatResponse(ApiModel):
    answer: str
    related_files: list[str] = Field(default_factory=list)
    supporting_chunks: list[ChatSupportingChunk] = Field(default_factory=list)
    mode: str
    source: str
    observability_status: str = "disabled"


class SuggestedIssueRead(ApiModel):
    id: str
    title: str
    category: str
    severity: str
    priority: str
    confidence: float
    effort: str
    description: str
    evidence: str
    related_files: list[str]
    suggested_fix: str
    github_issue_markdown: str
    created_at: datetime


class AnalysisSummaryRead(ApiModel):
    id: str
    repository_url: str | None = None
    repository_name: str
    branch: str | None = None
    source_type: str
    status: str
    analysis_mode: str
    detected_stack: list[str]
    languages: dict[str, int]
    files_analyzed: int
    total_files_seen: int
    risk_score: str
    summary: str | None = None
    architecture_summary: str | None = None
    duration_ms: int | None = None
    observability_trace_id: str | None = None
    observability_status: str
    observability_operations: list[str] = Field(default_factory=list)
    observability_steps: list[dict[str, object]] = Field(default_factory=list)
    observability_error: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisDetailRead(AnalysisSummaryRead):
    files: list[CodeFileRead] = Field(default_factory=list)
    chunks: list[CodeChunkRead] = Field(default_factory=list)
    issues: list[SuggestedIssueRead] = Field(default_factory=list)


class AnalysisCreateResponse(ApiModel):
    analysis_id: str
    status: str
    analysis: AnalysisDetailRead


class RepositoryAnalyzeRequest(ApiModel):
    repository_url: str
    branch: str | None = None
    analysis_mode: str = "quick"
    send_observability: bool = False


class ObservabilityRead(ApiModel):
    enabled: bool
    status: str
    trace_id: str | None = None
    app_name: str
    operations: list[str] = Field(default_factory=list)
    steps: list[dict[str, object]] = Field(default_factory=list)
    dashboard_url: str | None = None
    error: str | None = None
