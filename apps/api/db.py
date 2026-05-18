from collections.abc import Generator

from sqlalchemy import Engine, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from settings import get_settings


def _normalize_database_url(url: str) -> str:
    """Accept common hosted Postgres URLs while keeping SQLAlchemy explicit."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


settings = get_settings()
database_url = _normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine: Engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_repository_analysis_observability_columns()


def _ensure_repository_analysis_observability_columns() -> None:
    """MVP migration shim for existing local/dev DBs without Alembic."""
    required = {
        "observability_operations": "JSON DEFAULT '[]'",
        "observability_steps": "JSON DEFAULT '[]'",
        "observability_error": "VARCHAR",
    }
    inspector = inspect(engine)
    if "repositoryanalysis" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("repositoryanalysis")}
    missing = {name: ddl for name, ddl in required.items() if name not in existing}
    if not missing:
        return
    with engine.begin() as connection:
        for name, ddl in missing.items():
            connection.execute(text(f"ALTER TABLE repositoryanalysis ADD COLUMN {name} {ddl}"))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
