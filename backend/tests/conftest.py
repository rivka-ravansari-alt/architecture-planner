"""Pytest fixtures for Archsari tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.ai_client import BaseAIClient
from app.config.settings import settings
from app.core.database import Base, get_db
from app.core.dependencies import get_ai_client, get_current_user
from app.main import app
from tests.fixtures import VALID_AI_RESPONSE_JSON


class MockAIClient(BaseAIClient):
    def __init__(self, response: str = VALID_AI_RESPONSE_JSON) -> None:
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


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
def test_user(db_session: Session):
    from app.models import User

    user = User(
        google_sub="test-google-sub",
        email="test@example.com",
        name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_project(db_session: Session, test_user):
    from app.models import Project, RequirementAnswers

    project = Project(
        user_id=test_user.id,
        name="TaskFlow",
        description="A team task management product.",
        project_types=["web_app"],
        stage="mvp",
        expected_users="1000",
    )
    project.answers = RequirementAnswers(
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
def mock_ai_client():
    return MockAIClient()


@pytest.fixture
def mock_ai_success(mock_ai_client):
    return mock_ai_client


@pytest.fixture
def api_client(db_session: Session, test_user, ai_dirs, mock_ai_client, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    def override_get_ai_client():
        return mock_ai_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_ai_client] = override_get_ai_client
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
