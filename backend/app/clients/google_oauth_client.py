"""Google OAuth client wrapper."""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.config.params import OAUTH_PROVIDER_NAME, OAUTH_SCOPES, OAUTH_SERVER_METADATA_URL
from app.config.settings import settings


class GoogleOAuthClient:
    def __init__(self) -> None:
        self._oauth = OAuth()
        self._oauth.register(
            name=OAUTH_PROVIDER_NAME,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url=OAUTH_SERVER_METADATA_URL,
            client_kwargs={"scope": OAUTH_SCOPES},
        )

    @property
    def is_configured(self) -> bool:
        return settings.oauth_configured

    async def authorize_redirect(self, request, redirect_uri: str):
        return await self._oauth.google.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request):
        return await self._oauth.google.authorize_access_token(request)

    async def fetch_userinfo(self, token: dict) -> dict:
        userinfo = token.get("userinfo")
        if userinfo:
            return userinfo
        return await self._oauth.google.userinfo(token=token)
