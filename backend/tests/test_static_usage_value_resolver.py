"""Tests for resolving static usage values from project intake."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError
from app.services.static_usage_value_resolver import StaticUsageValueResolver


def test_resolve_users_and_stage_from_project():
    resolver = StaticUsageValueResolver()
    values = resolver.resolve(
        ["users", "stage"],
        expected_users=1000,
        stage="production",
        requirements={},
    )

    assert values == {"users": 1000, "stage": "production"}


def test_resolve_file_upload_static_values_from_requirements():
    resolver = StaticUsageValueResolver()
    values = resolver.resolve(
        ["documents_per_month", "average_document_size_mb"],
        expected_users=1000,
        stage="mvp",
        requirements={
            "file_uploads": {
                "enabled": True,
                "files_per_month": "1000-10000",
                "average_file_size": "1-10mb",
            }
        },
    )

    assert values["documents_per_month"] == 5_500
    assert values["average_document_size_mb"] == 5.5


def test_resolve_file_upload_static_values_default_to_zero_when_disabled():
    resolver = StaticUsageValueResolver()
    values = resolver.resolve(
        ["documents_per_month", "average_document_size_mb"],
        expected_users=1000,
        stage="mvp",
        requirements={"file_uploads": {"enabled": False}},
    )

    assert values == {"documents_per_month": 0, "average_document_size_mb": 0.0}


def test_resolve_notification_channel_count_from_requirements():
    resolver = StaticUsageValueResolver()
    values = resolver.resolve(
        ["notification_channel_count"],
        expected_users=1000,
        stage="mvp",
        requirements={
            "notifications": {
                "enabled": True,
                "channels": ["email", "push", "sms"],
            }
        },
    )

    assert values["notification_channel_count"] == 3


def test_resolve_notification_channel_count_zero_when_disabled():
    resolver = StaticUsageValueResolver()
    values = resolver.resolve(
        ["notification_channel_count"],
        expected_users=1000,
        stage="mvp",
        requirements={"notifications": {"enabled": False}},
    )

    assert values["notification_channel_count"] == 0


def test_resolve_ses_free_tier_active_from_stage():
    resolver = StaticUsageValueResolver()

    mvp = resolver.resolve(
        ["ses_free_tier_active"],
        expected_users=1000,
        stage="mvp",
        requirements={},
    )
    production = resolver.resolve(
        ["ses_free_tier_active"],
        expected_users=1000,
        stage="production",
        requirements={},
    )

    assert mvp["ses_free_tier_active"] == 1
    assert production["ses_free_tier_active"] == 0


def test_resolve_unknown_static_parameter_raises():
    resolver = StaticUsageValueResolver()

    with pytest.raises(BadRequestError, match="Could not resolve static usage parameters"):
        resolver.resolve(
            ["unknown_parameter"],
            expected_users=1000,
            stage="mvp",
            requirements={},
        )
