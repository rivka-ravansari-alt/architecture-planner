"""Database engine, session factory, and schema initialization."""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config.settings import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False, "timeout": 30},
            "poolclass": NullPool,
        }
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))


@event.listens_for(engine, "connect")
def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    dbapi_connection.execute("PRAGMA busy_timeout=30000")
    try:
        dbapi_connection.execute("PRAGMA journal_mode=WAL")
        dbapi_connection.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseInitializer:
    def __init__(self, db_engine=engine) -> None:
        self._engine = db_engine

    def initialize(self) -> None:
        import app.models  # noqa: F401 — register ORM models

        self._enable_sqlite_wal()
        Base.metadata.create_all(bind=self._engine)
        self._apply_migrations()

    def _enable_sqlite_wal(self) -> None:
        if not str(self._engine.url).startswith("sqlite"):
            return
        try:
            with self._engine.begin() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA synchronous=NORMAL"))
        except Exception as exc:
            logger.warning("SQLite WAL mode unavailable (%s); using default journal.", exc)

    def _apply_migrations(self) -> None:
        self._ensure_column(
            "projects",
            "architecture_summary",
            "ALTER TABLE projects ADD COLUMN architecture_summary TEXT DEFAULT ''",
        )
        self._ensure_column(
            "projects",
            "architecture_diagram",
            "ALTER TABLE projects ADD COLUMN architecture_diagram JSON",
        )
        self._ensure_column(
            "projects",
            "architecture_diagrams",
            "ALTER TABLE projects ADD COLUMN architecture_diagrams JSON",
        )
        self._ensure_column(
            "architecture_generation_requests",
            "project_id",
            "ALTER TABLE architecture_generation_requests ADD COLUMN project_id VARCHAR(36)",
        )
        self._ensure_column(
            "architecture_components",
            "component_type",
            "ALTER TABLE architecture_components ADD COLUMN component_type VARCHAR(40) DEFAULT 'api'",
        )
        self._ensure_column(
            "architecture_components",
            "implementation_options",
            "ALTER TABLE architecture_components ADD COLUMN implementation_options JSON",
        )
        self._ensure_column(
            "architecture_components",
            "source",
            "ALTER TABLE architecture_components ADD COLUMN source VARCHAR(20) DEFAULT 'ai_generated'",
        )
        self._ensure_column(
            "projects",
            "user_id",
            "ALTER TABLE projects ADD COLUMN user_id VARCHAR(36) REFERENCES users(id)",
        )
        self._ensure_column(
            "projects",
            "workflow_status",
            "ALTER TABLE projects ADD COLUMN workflow_status VARCHAR(40) DEFAULT 'DRAFT'",
        )
        for legacy_column in ("user_flow", "data_flow"):
            self._drop_column_if_exists("projects", legacy_column)

    def _ensure_column(self, table: str, column: str, ddl: str) -> None:
        inspector = inspect(self._engine)
        if table not in inspector.get_table_names():
            return
        existing = {col["name"] for col in inspector.get_columns(table)}
        if column in existing:
            return
        with self._engine.begin() as conn:
            conn.execute(text(ddl))

    def _drop_column_if_exists(self, table: str, column: str) -> None:
        inspector = inspect(self._engine)
        if table not in inspector.get_table_names():
            return
        existing = {col["name"] for col in inspector.get_columns(table)}
        if column not in existing:
            return
        with self._engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))


def init_db() -> None:
    DatabaseInitializer().initialize()
