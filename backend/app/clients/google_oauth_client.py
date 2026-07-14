"""Google OAuth client wrapper (Authlib + Starlette).

Wraps the Authlib OAuth registry so the rest of the app depends on a small,
explicit surface. Relies on Starlette's ``SessionMiddleware`` (registered in
``app.main``) to persist the OAuth state between the redirect and callback.
"""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

from app.config.params import (
    OAUTH_PROVIDER_NAME,
    OAUTH_SCOPES,
    OAUTH_SERVER_METADATA_URL,
)
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
    def _client(self):
        return self._oauth.create_client(OAUTH_PROVIDER_NAME)

    @property
    def is_configured(self) -> bool:
        return settings.oauth_configured

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        return await self._client.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request: Request) -> dict:
        return await self._client.authorize_access_token(request)
