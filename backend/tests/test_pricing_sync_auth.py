"""Tests for Cloud Scheduler auth on pricing sync."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config.settings import settings
from app.services.pricing_sync_auth import (
    SCHEDULER_PRINCIPAL,
    SCHEDULER_SECRET_HEADER,
    resolve_pricing_sync_principal,
)


@pytest.fixture
def scheduler_request():
    return SimpleNamespace(
        headers={},
        base_url="https://api.example.run.app/",
        url="https://api.example.run.app/api/admin/pricing/sync",
    )


def test_resolve_principal_from_logged_in_user(scheduler_request):
  principal = resolve_pricing_sync_principal(scheduler_request, user_id="user-123")
  assert principal == "user-123"


def test_resolve_principal_from_scheduler_secret(scheduler_request, monkeypatch):
    monkeypatch.setattr(settings, "pricing_sync_scheduler_secret", "top-secret")
    scheduler_request.headers = {SCHEDULER_SECRET_HEADER: "top-secret"}

    principal = resolve_pricing_sync_principal(scheduler_request, user_id=None)
    assert principal == SCHEDULER_PRINCIPAL


def test_rejects_wrong_scheduler_secret(scheduler_request, monkeypatch):
    monkeypatch.setattr(settings, "pricing_sync_scheduler_secret", "top-secret")
    scheduler_request.headers = {SCHEDULER_SECRET_HEADER: "wrong"}

    assert resolve_pricing_sync_principal(scheduler_request, user_id=None) is None
