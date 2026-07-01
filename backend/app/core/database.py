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
        self._migrate_legacy_project_components_table()
        Base.metadata.create_all(bind=self._engine)
        self._apply_migrations()
        self._seed_component_catalog()
        self._backfill_component_catalog_categories()
        self._backfill_component_catalog_cloud_options()

    def _enable_sqlite_wal(self) -> None:
        if not str(self._engine.url).startswith("sqlite"):
            return
        try:
            with self._engine.begin() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA synchronous=NORMAL"))
        except Exception as exc:
            logger.warning("SQLite WAL mode unavailable (%s); using default journal.", exc)

    def _migrate_legacy_project_components_table(self) -> None:
        inspector = inspect(self._engine)
        tables = set(inspector.get_table_names())
        if "architecture_components" not in tables or "project_components" in tables:
            return
        columns = {col["name"] for col in inspector.get_columns("architecture_components")}
        if "project_id" not in columns:
            return
        with self._engine.begin() as conn:
            conn.execute(text("ALTER TABLE architecture_components RENAME TO project_components"))

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
            "project_components",
            "component_type",
            "ALTER TABLE project_components ADD COLUMN component_type VARCHAR(40) DEFAULT 'api'",
        )
        self._ensure_column(
            "project_components",
            "implementation_options",
            "ALTER TABLE project_components ADD COLUMN implementation_options JSON",
        )
        self._ensure_column(
            "project_components",
            "source",
            "ALTER TABLE project_components ADD COLUMN source VARCHAR(20) DEFAULT 'ai_generated'",
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
        self._ensure_column(
            "architecture_components",
            "category",
            "ALTER TABLE architecture_components ADD COLUMN category VARCHAR(40) "
            "DEFAULT 'main_architecture' NOT NULL",
        )
        for legacy_column in ("user_flow", "data_flow"):
            self._drop_column_if_exists("projects", legacy_column)

        self._ensure_column(
            "cost_estimates",
            "required_monthly_low",
            "ALTER TABLE cost_estimates ADD COLUMN required_monthly_low FLOAT DEFAULT 0.0",
        )
        self._ensure_column(
            "cost_estimates",
            "required_monthly_high",
            "ALTER TABLE cost_estimates ADD COLUMN required_monthly_high FLOAT DEFAULT 0.0",
        )
        self._ensure_column(
            "cost_estimates",
            "optional_monthly_low",
            "ALTER TABLE cost_estimates ADD COLUMN optional_monthly_low FLOAT DEFAULT 0.0",
        )
        self._ensure_column(
            "cost_estimates",
            "optional_monthly_high",
            "ALTER TABLE cost_estimates ADD COLUMN optional_monthly_high FLOAT DEFAULT 0.0",
        )
        self._ensure_column(
            "cost_estimates",
            "unknown_items",
            "ALTER TABLE cost_estimates ADD COLUMN unknown_items JSON",
        )
        self._ensure_column(
            "cost_estimates",
            "warnings",
            "ALTER TABLE cost_estimates ADD COLUMN warnings JSON",
        )
        self._ensure_column(
            "cost_estimates",
            "component_breakdown",
            "ALTER TABLE cost_estimates ADD COLUMN component_breakdown JSON",
        )
        self._ensure_column(
            "cost_estimates",
            "pricing_debug_table",
            "ALTER TABLE cost_estimates ADD COLUMN pricing_debug_table JSON",
        )
        self._ensure_column(
            "cost_estimates",
            "calculator_version",
            "ALTER TABLE cost_estimates ADD COLUMN calculator_version VARCHAR(40) DEFAULT ''",
        )
        self._ensure_column(
            "requirement_answers",
            "usage_profile",
            "ALTER TABLE requirement_answers ADD COLUMN usage_profile JSON",
        )

    def _seed_component_catalog(self) -> None:
        from app.repositories.component_catalog_repository import ComponentCatalogRepository

        with SessionLocal() as session:
            ComponentCatalogRepository(session).seed_if_empty()

    def _backfill_component_catalog_categories(self) -> None:
        from app.repositories.component_catalog_repository import ComponentCatalogRepository

        with SessionLocal() as session:
            ComponentCatalogRepository(session).backfill_categories()

    def _backfill_component_catalog_cloud_options(self) -> None:
        from app.repositories.component_catalog_repository import ComponentCatalogRepository

        with SessionLocal() as session:
            ComponentCatalogRepository(session).backfill_cloud_options_from_seed()

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
