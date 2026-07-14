"""FastAPI dependency injection helpers (Firestore-backed)."""

from __future__ import annotations

from fastapi import Depends, Request
from google.cloud import firestore

from app.api.controllers.auth_controller import AuthController
from app.api.controllers.project_controller import ProjectController
from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.clients.firestore_client import get_firestore_client
from app.clients.google_oauth_client import GoogleOAuthClient
from app.config.params import ERR_NOT_AUTHENTICATED
from app.config.settings import settings
from app.core.exceptions import UnauthorizedError
from app.repositories.architecture_category_repository import (
    ArchitectureCategoryRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut
from app.services.architecture_component_selection_service import (
    ArchitectureComponentSelectionService,
)
from app.services.architecture_component_service import ArchitectureComponentService
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.utils.jwt import JwtService

_oauth_client = GoogleOAuthClient()


def get_firestore() -> firestore.Client:
    return get_firestore_client()


def get_jwt_service() -> JwtService:
    return JwtService()


def get_oauth_client() -> GoogleOAuthClient:
    return _oauth_client


def get_user_repository(
    client: firestore.Client = Depends(get_firestore),
) -> UserRepository:
    return UserRepository(client)


def get_project_repository(
    client: firestore.Client = Depends(get_firestore),
) -> ProjectRepository:
    return ProjectRepository(client)


def get_architecture_category_repository(
    client: firestore.Client = Depends(get_firestore),
) -> ArchitectureCategoryRepository:
    return ArchitectureCategoryRepository(client)


def get_ai_client() -> BaseAIClient:
    return AIClientFactory.create()


def get_architecture_component_selection_service(
    ai_client: BaseAIClient = Depends(get_ai_client),
) -> ArchitectureComponentSelectionService:
    return ArchitectureComponentSelectionService(ai_client)


def get_architecture_component_service(
    projects: ProjectRepository = Depends(get_project_repository),
    categories: ArchitectureCategoryRepository = Depends(
        get_architecture_category_repository
    ),
    selection_service: ArchitectureComponentSelectionService = Depends(
        get_architecture_component_selection_service
    ),
) -> ArchitectureComponentService:
    return ArchitectureComponentService(projects, categories, selection_service)


def get_auth_service(
    oauth_client: GoogleOAuthClient = Depends(get_oauth_client),
    users: UserRepository = Depends(get_user_repository),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> AuthService:
    return AuthService(oauth_client, users, jwt_service)


def get_project_service(
    projects: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
    return ProjectService(projects)


def get_auth_controller(
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthController:
    return AuthController(auth_service)


def get_project_controller(
    project_service: ProjectService = Depends(get_project_service),
    architecture_component_service: ArchitectureComponentService = Depends(
        get_architecture_component_service
    ),
) -> ProjectController:
    return ProjectController(project_service, architecture_component_service)


def get_optional_user(
    request: Request,
    users: UserRepository = Depends(get_user_repository),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> UserOut | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None

    user_id = jwt_service.decode_access_token(token)
    if not user_id:
        return None

    return users.find_by_id(user_id)


def get_current_user(
    user: UserOut | None = Depends(get_optional_user),
) -> UserOut:
    if user is None:
        raise UnauthorizedError(ERR_NOT_AUTHENTICATED)
    return user
