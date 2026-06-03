from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    # SQLite needs this flag when used across threads (uvicorn workers).
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_column(table: str, column: str, ddl: str) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    if column in existing:
        return
    with engine.begin() as conn:
        conn.execute(text(ddl))


def _drop_column_if_exists(table: str, column: str) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    if column not in existing:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))


def init_db() -> None:
    # Import models so they register on the metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_column(
        "projects",
        "architecture_summary",
        "ALTER TABLE projects ADD COLUMN architecture_summary TEXT DEFAULT ''",
    )
    _ensure_column(
        "projects",
        "architecture_diagram",
        "ALTER TABLE projects ADD COLUMN architecture_diagram JSON",
    )
    _ensure_column(
        "projects",
        "architecture_diagrams",
        "ALTER TABLE projects ADD COLUMN architecture_diagrams JSON",
    )
    _ensure_column(
        "architecture_generation_requests",
        "project_id",
        "ALTER TABLE architecture_generation_requests ADD COLUMN project_id VARCHAR(36)",
    )
    _ensure_column(
        "architecture_components",
        "component_type",
        "ALTER TABLE architecture_components ADD COLUMN component_type VARCHAR(40) DEFAULT 'api'",
    )
    # Removed from the model when main_flow replaced user_flow/data_flow.
    for legacy_column in ("user_flow", "data_flow"):
        _drop_column_if_exists("projects", legacy_column)
