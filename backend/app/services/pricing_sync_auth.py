"""Authentication helpers for scheduled pricing sync calls."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token

from app.config.settings import settings

if TYPE_CHECKING:
    from fastapi import Request

SCHEDULER_SECRET_HEADER = "X-Scheduler-Secret"
SCHEDULER_PRINCIPAL = "cloud-scheduler"


def _allowed_scheduler_service_accounts() -> frozenset[str]:
    raw = settings.pricing_sync_scheduler_service_accounts.strip()
    if not raw:
        return frozenset()
    return frozenset(
        email.strip().lower()
        for email in raw.split(",")
        if email.strip()
    )


def _resolve_oidc_audience(request: Request) -> str:
    if settings.pricing_sync_scheduler_audience.strip():
        return settings.pricing_sync_scheduler_audience.strip()
    return str(request.base_url).rstrip("/")


def _verify_scheduler_secret(request: Request) -> bool:
    expected = settings.pricing_sync_scheduler_secret.strip()
    if not expected:
        return False
    provided = request.headers.get(SCHEDULER_SECRET_HEADER)
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)


def _verify_scheduler_oidc(request: Request) -> str | None:
    allowed_accounts = _allowed_scheduler_service_accounts()
    if not allowed_accounts:
        return None

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None

    try:
        claims = id_token.verify_oauth2_token(
            token,
            google_auth_requests.Request(),
            audience=_resolve_oidc_audience(request),
        )
    except ValueError:
        return None

    email = str(claims.get("email", "")).lower()
    if email not in allowed_accounts:
        return None
    return email or SCHEDULER_PRINCIPAL


def resolve_pricing_sync_principal(request: Request, *, user_id: str | None) -> str | None:
    """Return a principal id when the caller is an admin user or trusted scheduler."""
    if user_id:
        return user_id
    if _verify_scheduler_secret(request):
        return SCHEDULER_PRINCIPAL
    return _verify_scheduler_oidc(request)
