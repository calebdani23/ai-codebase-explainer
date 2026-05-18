from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from db import get_session, init_db
from models import RepositoryAnalysis
from schemas import AnalysisCreateResponse, AnalysisDetailRead, AnalysisSummaryRead, ChatRequest, ChatResponse, DemoAnalyzeRequest, ObservabilityRead, RepositoryAnalyzeRequest, SuggestedIssueRead
from services.chat import answer_analysis_chat
from services.demo_analysis import create_demo_analysis
from services.exporting import build_markdown_export
from services.repository_analysis import analyze_public_github_repository
from settings import get_settings


settings = get_settings()

app = FastAPI(
    title="AI Codebase Explainer API",
    description="Backend API for repository understanding, architecture review and issue triage.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-codebase-explainer-api"}


@app.get("/api/config")
async def public_config() -> dict[str, object]:
    return {
        "demo_mode": settings.demo_mode,
        "observability_enabled": settings.observability_enabled,
        "service": "ai-codebase-explainer-api",
    }


@app.post("/api/demo/analyze", response_model=AnalysisCreateResponse)
async def analyze_demo_repo(
    payload: DemoAnalyzeRequest | None = None,
    session: Session = Depends(get_session),
) -> AnalysisCreateResponse:
    request = payload or DemoAnalyzeRequest()
    try:
        analysis = await create_demo_analysis(
            session=session,
            demo_repo=request.demo_repo,
            analysis_mode=request.analysis_mode,
            send_observability=request.send_observability,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _ = analysis.files, analysis.chunks, analysis.issues
    return AnalysisCreateResponse(analysis_id=analysis.id, status=analysis.status, analysis=analysis)


@app.post("/api/repositories/analyze", response_model=AnalysisCreateResponse)
async def analyze_github_repo(
    payload: RepositoryAnalyzeRequest,
    session: Session = Depends(get_session),
) -> AnalysisCreateResponse:
    try:
        analysis = await analyze_public_github_repository(
            session=session,
            repository_url=payload.repository_url,
            branch=payload.branch,
            analysis_mode=payload.analysis_mode,
            send_observability=payload.send_observability,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _ = analysis.files, analysis.chunks, analysis.issues
    return AnalysisCreateResponse(analysis_id=analysis.id, status=analysis.status, analysis=analysis)


@app.get("/api/analyses", response_model=list[AnalysisSummaryRead])
async def list_analyses(
    status: str | None = None,
    repository_name: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[RepositoryAnalysis]:
    statement = select(RepositoryAnalysis)
    if status:
        statement = statement.where(RepositoryAnalysis.status == status)
    if repository_name:
        statement = statement.where(RepositoryAnalysis.repository_name.contains(repository_name))
    statement = statement.order_by(RepositoryAnalysis.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisDetailRead)
async def get_analysis(analysis_id: str, session: Session = Depends(get_session)) -> RepositoryAnalysis:
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    # Touch relationships while the session is open so response serialization includes them.
    _ = analysis.files, analysis.chunks, analysis.issues
    return analysis


@app.get("/api/analyses/{analysis_id}/issues", response_model=list[SuggestedIssueRead])
async def get_analysis_issues(analysis_id: str, session: Session = Depends(get_session)):
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis.issues


@app.post("/api/analyses/{analysis_id}/chat", response_model=ChatResponse)
async def chat_with_analysis(analysis_id: str, payload: ChatRequest, session: Session = Depends(get_session)) -> dict[str, object]:
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    _ = analysis.files, analysis.chunks, analysis.issues
    return await answer_analysis_chat(analysis, payload.message)


@app.get("/api/analyses/{analysis_id}/observability", response_model=ObservabilityRead)
async def get_analysis_observability(analysis_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "enabled": settings.observability_enabled,
        "status": analysis.observability_status,
        "trace_id": analysis.observability_trace_id,
        "app_name": settings.observability_app_name,
        "operations": analysis.observability_operations or [],
        "steps": analysis.observability_steps or [],
        "dashboard_url": settings.observability_api_url.rstrip("/") if settings.observability_api_url else None,
        "error": analysis.observability_error,
    }


@app.get("/api/analyses/{analysis_id}/export.md", response_class=PlainTextResponse)
async def export_analysis_markdown(analysis_id: str, session: Session = Depends(get_session)) -> str:
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    _ = analysis.files, analysis.chunks, analysis.issues
    return build_markdown_export(analysis)


@app.get("/api/analyses/{analysis_id}/export.json", response_model=AnalysisDetailRead)
async def export_analysis_json(analysis_id: str, session: Session = Depends(get_session)) -> RepositoryAnalysis:
    analysis = session.get(RepositoryAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    _ = analysis.files, analysis.chunks, analysis.issues
    return analysis
