"""Authentication business logic (Google OAuth -> Firestore user -> JWT)."""

from __future__ import annotations

from starlette.requests import Request

from app.clients.google_oauth_client import GoogleOAuthClient
from app.config.params import ERR_GOOGLE_SUB_MISSING, ERR_OAUTH_NOT_CONFIGURED
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut
from app.utils.jwt import JwtService


class AuthService:
    def __init__(
        self,
        oauth_client: GoogleOAuthClient,
        user_repository: UserRepository,
        jwt_service: JwtService,
    ) -> None:
        self._oauth = oauth_client
        self._users = user_repository
        self._jwt = jwt_service

    def ensure_oauth_configured(self) -> None:
        if not self._oauth.is_configured:
            raise ServiceUnavailableError(ERR_OAUTH_NOT_CONFIGURED)

    async def start_google_login(self, request: Request, redirect_uri: str):
        self.ensure_oauth_configured()
        return await self._oauth.authorize_redirect(request, redirect_uri)

    async def complete_google_login(self, request: Request) -> str:
        """Complete the OAuth exchange, upsert the user, and return a JWT."""

        self.ensure_oauth_configured()
        token = await self._oauth.authorize_access_token(request)
        userinfo = token.get("userinfo") or {}

        google_sub = userinfo.get("sub")
        if not google_sub:
            raise BadRequestError(ERR_GOOGLE_SUB_MISSING)

        user: UserOut = self._users.upsert_by_google_sub(
            google_sub=google_sub,
            email=userinfo.get("email", ""),
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture"),
        )
        return self._jwt.create_access_token(user.id)
