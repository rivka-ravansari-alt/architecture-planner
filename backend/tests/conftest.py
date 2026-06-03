"""Pytest fixtures for Archsari tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from tests.fixtures import VALID_AI_RESPONSE_JSON


@pytest.fixture
def ai_dirs(tmp_path, monkeypatch):
    prompts = tmp_path / "prompts"
    outputs = tmp_path / "outputs"
    monkeypatch.setattr(settings, "ai_prompts_dir", str(prompts))
    monkeypatch.setattr(settings, "ai_outputs_dir", str(outputs))
    return prompts, outputs


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session_factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_project(db_session: Session):
    from app import models

    project = models.Project(
        name="TaskFlow",
        description="A team task management product.",
        project_types=["web_app"],
        stage="mvp",
        expected_users="1000",
    )
    project.answers = models.RequirementAnswers(
        auth=True,
        file_upload=True,
        background_processing=False,
        dashboards=False,
        ai=False,
        payments=False,
        include_edge_cases=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def mock_ai_success(monkeypatch):
    def _fake(_prompt: str) -> str:
        return VALID_AI_RESPONSE_JSON

    monkeypatch.setattr("app.services.generation.generate_architecture", _fake)
    return _fake


@pytest.fixture
def api_client(db_session: Session, ai_dirs, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
