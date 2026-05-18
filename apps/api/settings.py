from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    demo_mode: bool = True
    database_url: str = "sqlite:///./local_dev.db"
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://YOUR_GITHUB_USERNAME.github.io"
    )
    port: int = 8000

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    github_token: str = ""

    max_repo_size_mb: int = 25
    max_file_size_kb: int = 300
    max_files_analyzed: int = 300

    observability_enabled: bool = False
    observability_api_url: str = ""
    observability_ingest_api_key: str = ""
    observability_app_name: str = "ai-codebase-explainer"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
