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
from app.repositories.component_catalog_repository import ComponentCatalogRepository
from app.services.catalog_service import CatalogService
from app.services.cloud_defaults_service import CloudDefaultsService
from app.services.component_mapper_service import ComponentMapperService
from app.services.prompt_builder_service import PromptBuilderService
from app.validators.ai_response_validator import AIResponseValidator
from tests.fixtures import VALID_AI_RESPONSE_JSON


def seed_component_catalog(db_session: Session) -> ComponentCatalogRepository:
    repo = ComponentCatalogRepository(db_session)
    repo.seed_if_empty()
    return repo


def build_catalog_services(db_session: Session) -> tuple[CatalogService, CloudDefaultsService]:
    repo = seed_component_catalog(db_session)
    catalog = CatalogService(db_session, repo)
    cloud = CloudDefaultsService(repo)
    return catalog, cloud


class MockAIClient(BaseAIClient):
    def __init__(self, response: str = VALID_AI_RESPONSE_JSON) -> None:
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


@pytest.fixture
def ai_dirs(tmp_path, monkeypatch):
    storage = tmp_path / "object-storage"
    monkeypatch.setattr(settings, "object_storage_provider", "local")
    monkeypatch.setattr(settings, "object_storage_local_root", str(storage))
    return storage


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
    seed_component_catalog(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def catalog_service(db_session):
    return CatalogService(db_session)


@pytest.fixture
def cloud_defaults_service(db_session):
    _, cloud = build_catalog_services(db_session)
    return cloud


@pytest.fixture
def ai_validator(catalog_service, cloud_defaults_service):
    return AIResponseValidator(cloud_defaults_service, catalog_service)


@pytest.fixture
def prompt_builder(catalog_service):
    return PromptBuilderService(catalog_service)


@pytest.fixture
def component_mapper(catalog_service):
    return ComponentMapperService(catalog_service)


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
