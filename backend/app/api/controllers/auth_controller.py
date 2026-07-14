"""Authentication HTTP controller."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.config.params import SESSION_COOKIE_PATH, SESSION_COOKIE_SAMESITE
from app.config.settings import settings
from app.schemas.auth import UserOut
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    async def google_login(self, request: Request):
        return await self._auth.start_google_login(request, settings.google_redirect_uri)

    async def google_callback(self, request: Request) -> RedirectResponse:
        token = await self._auth.complete_google_login(request)
        response = RedirectResponse(url=settings.frontend_url)
        self._set_session_cookie(response, token)
        return response

    def current_user(self, user: UserOut | None) -> UserOut | None:
        return user

    def logout(self) -> Response:
        response = Response(status_code=204)
        response.delete_cookie(
            key=settings.session_cookie_name,
            path=SESSION_COOKIE_PATH,
        )
        return response

    def _set_session_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=settings.session_cookie_name,
            value=token,
            max_age=settings.jwt_expire_minutes * 60,
            httponly=True,
            secure=settings.session_cookie_secure,
            samesite=SESSION_COOKIE_SAMESITE,
            path=SESSION_COOKIE_PATH,
        )
