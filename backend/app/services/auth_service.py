"""Authentication business logic."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.clients.google_oauth_client import GoogleOAuthClient
from app.config.params import ERR_GOOGLE_SUB_MISSING, ERR_OAUTH_NOT_CONFIGURED
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.utils.jwt import JwtService


@dataclass
class GoogleUserProfile:
    google_sub: str
    email: str
    name: str
    picture: str | None


class AuthService:
    def __init__(
        self,
        db: Session,
        *,
        user_repo: UserRepository | None = None,
        jwt_service: JwtService | None = None,
        oauth_client: GoogleOAuthClient | None = None,
    ) -> None:
        self._user_repo = user_repo or UserRepository(db)
        self._jwt = jwt_service or JwtService()
        self._oauth = oauth_client or GoogleOAuthClient()

    @property
    def oauth_client(self) -> GoogleOAuthClient:
        return self._oauth

    def ensure_oauth_configured(self) -> None:
        if not self._oauth.is_configured:
            raise ServiceUnavailableError(ERR_OAUTH_NOT_CONFIGURED)

    async def start_google_login(self, request):
        self.ensure_oauth_configured()
        from app.config.settings import settings

        return await self._oauth.authorize_redirect(request, settings.google_redirect_uri)

    async def complete_google_login(self, request) -> tuple[User, str]:
        self.ensure_oauth_configured()
        token = await self._oauth.authorize_access_token(request)
        profile = self._parse_google_profile(await self._oauth.fetch_userinfo(token))
        user = self._upsert_user(profile)
        self._user_repo.commit()
        self._user_repo.refresh(user)
        session_token = self._jwt.create_access_token(user.id)
        return user, session_token

    def _parse_google_profile(self, userinfo: dict) -> GoogleUserProfile:
        google_sub = userinfo.get("sub")
        if not google_sub:
            raise BadRequestError(ERR_GOOGLE_SUB_MISSING)
        return GoogleUserProfile(
            google_sub=google_sub,
            email=userinfo.get("email") or "",
            name=userinfo.get("name") or "",
            picture=userinfo.get("picture"),
        )

    def _upsert_user(self, profile: GoogleUserProfile) -> User:
        user = self._user_repo.find_by_google_sub(profile.google_sub)
        if user is None:
            return self._user_repo.create(
                google_sub=profile.google_sub,
                email=profile.email,
                name=profile.name,
                picture=profile.picture,
            )
        return self._user_repo.update_profile(
            user,
            email=profile.email,
            name=profile.name,
            picture=profile.picture,
        )
