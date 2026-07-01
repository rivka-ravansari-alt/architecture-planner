"""Tests for the provider-independent Usage Estimator."""

from __future__ import annotations

import pytest

from app.schemas.domain import MappedComponent
from app.services.usage_estimation import ProductCapabilities, UsageEstimator


def _service_component() -> MappedComponent:
    return MappedComponent(
        key="service",
        name="API",
        component_type="api",
        reason="Backend",
        category="core",
        optional=False,
        order=0,
        cloud={"aws": [], "gcp": ["Cloud Run"], "azure": []},
        implementation_options={},
    )


def _storage_component() -> MappedComponent:
    return MappedComponent(
        key="object_storage",
        name="Object Storage",
        component_type="object_storage",
        reason="Files",
        category="core",
        optional=True,
        order=1,
        cloud={"aws": [], "gcp": ["Cloud Storage"], "azure": []},
        implementation_options={},
    )


def test_usage_estimator_derives_requests_from_users():
    estimate = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[_service_component()],
        capabilities=ProductCapabilities(),
    )
    global_usage = estimate.global_consumption
    assert global_usage.monthly_active_users == 100
    # Baseline moderate profile: 100 users × 12 actions/day × 25 active days
    assert global_usage.monthly_requests == pytest.approx(30_000)
    assert global_usage.cpu_seconds > 0
    assert global_usage.memory_gib_seconds > 0


def test_capabilities_increase_relevant_usage():
    base = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        capabilities=ProductCapabilities(),
    )
    with_ai = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        capabilities=ProductCapabilities(ai=True),
    )
    assert with_ai.global_consumption.input_tokens > base.global_consumption.input_tokens
    assert with_ai.global_consumption.output_tokens > base.global_consumption.output_tokens

    with_uploads = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        capabilities=ProductCapabilities(file_upload=True),
    )
    assert with_uploads.global_consumption.storage_gb > base.global_consumption.storage_gb


def test_component_allocator_assigns_only_relevant_metrics():
    components = [_service_component(), _storage_component()]
    estimate = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=components,
        capabilities=ProductCapabilities(),
    )
    service_usage = estimate.component_consumption["service"].to_pricing_metrics()
    storage_usage = estimate.component_consumption["object_storage"].to_pricing_metrics()

    assert service_usage["monthly_requests"] > 0
    assert service_usage["cpu_seconds"] > 0
    assert service_usage.get("storage_gb", 0) == 0

    assert storage_usage["storage_gb"] > 0
    assert storage_usage.get("cpu_seconds", 0) == 0
    assert storage_usage.get("monthly_requests", 0) == 0


def test_production_stage_scales_traffic():
    mvp = UsageEstimator().estimate(
        expected_users="1000",
        stage="mvp",
        components=[],
        capabilities=ProductCapabilities(),
    )
    prod = UsageEstimator().estimate(
        expected_users="1000",
        stage="production",
        components=[],
        capabilities=ProductCapabilities(),
    )
    assert prod.global_consumption.monthly_requests > mvp.global_consumption.monthly_requests


def test_usage_profile_drives_higher_activity_than_baseline():
    baseline = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        usage_profile={
            "monthly_active_users": "100",
            "user_activity": "light",
        },
    )
    active = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        usage_profile={
            "monthly_active_users": "100",
            "user_activity": "very_heavy",
            "background_jobs": "heavy",
            "ai_enabled": True,
            "ai_requests_per_user_per_day": "5_20",
            "file_uploads_enabled": True,
            "files_per_month": "10k_100k",
            "average_file_size": "large",
            "notification_channels": ["email", "push"],
            "notifications_per_month": "10k_100k",
        },
    )
    assert active.global_consumption.monthly_requests > baseline.global_consumption.monthly_requests
    assert active.global_consumption.storage_gb > baseline.global_consumption.storage_gb
    assert active.global_consumption.ai_requests > baseline.global_consumption.ai_requests


def test_usage_profile_estimates_storage_without_user_input():
    light = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        usage_profile={
            "monthly_active_users": "100",
            "user_activity": "light",
        },
    )
    heavy_uploads = UsageEstimator().estimate(
        expected_users="1000",
        stage="mvp",
        components=[],
        usage_profile={
            "monthly_active_users": "1000",
            "user_activity": "heavy",
            "file_uploads_enabled": True,
            "files_per_month": "1k_10k",
            "average_file_size": "large",
        },
    )
    assert heavy_uploads.global_consumption.storage_gb > light.global_consumption.storage_gb
    assert heavy_uploads.global_consumption.database_storage_gb > light.global_consumption.database_storage_gb


def test_usage_profile_notification_channels_split_volume():
    estimate = UsageEstimator().estimate(
        expected_users="1000",
        stage="mvp",
        components=[],
        usage_profile={
            "monthly_active_users": "1000",
            "user_activity": "moderate",
            "notification_channels": ["email", "sms"],
            "notifications_per_month": "1k_10k",
        },
    )
    usage = estimate.global_consumption
    assert usage.emails_sent == pytest.approx(2500.0)
    assert usage.sms_messages == pytest.approx(2500.0)
    assert usage.push_notifications == 0.0
