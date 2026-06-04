"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.config.params import (
    ERR_INVALID_SESSION,
    ERR_NOT_AUTHENTICATED,
    ERR_USER_NOT_FOUND,
)
from app.config.settings import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.catalog_service import CatalogService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService
from app.utils.jwt import JwtService


def get_jwt_service() -> JwtService:
    return JwtService()


def get_ai_client() -> BaseAIClient:
    return AIClientFactory.create()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


def get_generation_service(
    db: Session = Depends(get_db),
    ai_client: BaseAIClient = Depends(get_ai_client),
) -> GenerationService:
    return GenerationService(db, ai_client=ai_client)


def get_catalog_service() -> CatalogService:
    return CatalogService()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise UnauthorizedError(ERR_NOT_AUTHENTICATED)

    user_id = jwt_service.decode_access_token(token)
    if not user_id:
        raise UnauthorizedError(ERR_INVALID_SESSION)

    user = UserRepository(db).find_by_id(user_id)
    if user is None:
        raise UnauthorizedError(ERR_USER_NOT_FOUND)
    return user
