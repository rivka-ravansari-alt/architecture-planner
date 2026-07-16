"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth_router, health_router, project_router
from app.config.params import OAUTH_SESSION_COOKIE, OAUTH_SESSION_MAX_AGE_SECONDS
from app.config.settings import settings
from app.core.exceptions import (
    AIClientError,
    AIValidationError,
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
    # Firestore uses lazy-initialized clients (ADC), so there is nothing to
    # initialize at startup for Step 1 (auth + project intake).
    logger.info("%s started (Step 1: auth + project intake on Firestore).", settings.app_name)
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
    def _error_response(status_code: int, message: str) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": message})

    @application.exception_handler(UnauthorizedError)
    async def unauthorized_handler(_request: Request, exc: UnauthorizedError):
        return _error_response(status.HTTP_401_UNAUTHORIZED, exc.message)

    @application.exception_handler(ForbiddenError)
    async def forbidden_handler(_request: Request, exc: ForbiddenError):
        return _error_response(status.HTTP_403_FORBIDDEN, exc.message)

    @application.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return _error_response(status.HTTP_404_NOT_FOUND, exc.message)

    @application.exception_handler(BadRequestError)
    async def bad_request_handler(_request: Request, exc: BadRequestError):
        return _error_response(status.HTTP_400_BAD_REQUEST, exc.message)

    @application.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(_request: Request, exc: ServiceUnavailableError):
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, exc.message)

    @application.exception_handler(ArchitectureGenerationError)
    async def generation_failed_handler(_request: Request, exc: ArchitectureGenerationError):
        return _error_response(status.HTTP_502_BAD_GATEWAY, exc.message)

    @application.exception_handler(AIClientError)
    async def ai_client_handler(_request: Request, exc: AIClientError):
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, exc.message)

    @application.exception_handler(AIValidationError)
    async def ai_validation_handler(_request: Request, exc: AIValidationError):
        logger.error("AI validation failed: %s", exc.message)
        return _error_response(status.HTTP_502_BAD_GATEWAY, exc.message)


def _register_routes(application: FastAPI) -> None:
    application.include_router(health_router, prefix="/api")
    application.include_router(auth_router, prefix="/api")
    application.include_router(project_router, prefix="/api")


app = create_app()
