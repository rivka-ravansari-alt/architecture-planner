"""Authentication HTTP controller."""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from app.config.params import SESSION_COOKIE_PATH, SESSION_COOKIE_SAMESITE
from app.config.settings import settings
from app.core.exceptions import BadRequestError
from app.models import User
from app.schemas.auth import UserOut
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class AuthController:
    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    async def google_login(self, request: Request):
        return await self._auth.start_google_login(request)

    async def google_callback(self, request: Request) -> RedirectResponse:
        try:
            _user, session_token = await self._auth.complete_google_login(request)
        except Exception as exc:
            logger.exception("Google OAuth callback failed")
            raise BadRequestError(f"Failed to complete Google sign-in: {exc}") from exc

        response = RedirectResponse(url=settings.frontend_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(**self._session_cookie(session_token))
        return response

    def current_user(self, user: User) -> UserOut:
        return UserOut.model_validate(user)

    def logout(self) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        response.set_cookie(**self._clear_session_cookie())
        return response

    @staticmethod
    def _session_cookie(token: str) -> dict:
        return {
            "key": settings.session_cookie_name,
            "value": token,
            "httponly": True,
            "secure": settings.session_cookie_secure,
            "samesite": SESSION_COOKIE_SAMESITE,
            "path": SESSION_COOKIE_PATH,
            "max_age": settings.jwt_expire_minutes * 60,
        }

    @staticmethod
    def _clear_session_cookie() -> dict:
        return {
            "key": settings.session_cookie_name,
            "value": "",
            "httponly": True,
            "secure": settings.session_cookie_secure,
            "samesite": SESSION_COOKIE_SAMESITE,
            "path": SESSION_COOKIE_PATH,
            "max_age": 0,
        }
