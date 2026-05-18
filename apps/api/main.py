from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
