"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth_router, health_router, project_router
from app.config.params import OAUTH_SESSION_COOKIE, OAUTH_SESSION_MAX_AGE_SECONDS
from app.config.settings import settings
from app.core.database import init_db
from app.core.dependencies import get_google_oauth_client
from app.core.exceptions import (
    AIClientError,
    ArchitectureGenerationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    from app.config.settings import Settings

    runtime_settings = Settings()
    if runtime_settings.openai_api_key:
        logger.info("AI generation uses OpenAI model %s.", runtime_settings.openai_model)
    else:
        logger.warning("OpenAI API key is not configured; /generate will fail.")
    if runtime_settings.oauth_configured:
        await get_google_oauth_client().ensure_metadata_loaded()
        logger.info("Google OAuth OIDC metadata cached.")
    yield


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    _register_middleware(application)
    _register_exception_handlers(application)
    _register_routes(application)
    return application


def _register_middleware(application: FastAPI) -> None:
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.jwt_secret,
        session_cookie=OAUTH_SESSION_COOKIE,
        max_age=OAUTH_SESSION_MAX_AGE_SECONDS,
    )


def _register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_request: Request, exc: UnauthorizedError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)

    @application.exception_handler(ForbiddenError)
    async def forbidden_handler(_request: Request, exc: ForbiddenError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    @application.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

    @application.exception_handler(BadRequestError)
    async def bad_request_handler(_request: Request, exc: BadRequestError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

    @application.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(_request: Request, exc: ServiceUnavailableError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message)

    @application.exception_handler(ArchitectureGenerationError)
    async def generation_failed_handler(_request: Request, exc: ArchitectureGenerationError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)

    @application.exception_handler(AIClientError)
    async def ai_client_handler(_request: Request, exc: AIClientError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message)


def _register_routes(application: FastAPI) -> None:
    application.include_router(health_router, prefix="/api")
    application.include_router(auth_router, prefix="/api")
    application.include_router(project_router, prefix="/api")


app = create_app()
