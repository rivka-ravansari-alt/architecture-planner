"""Unit tests for usage input building."""

from __future__ import annotations

from app.schemas.global_usage_model import GlobalUsageModelPayload, UsageParameterEstimate
from app.services.usage_inputs_builder import build_usage_inputs


def test_build_usage_inputs_derives_requests_per_month():
    payload = GlobalUsageModelPayload(
        llm={
            "api_requests_per_user_per_month": UsageParameterEstimate(
                value=50,
                reason="Typical API usage.",
            ),
        },
        static={"users": 1000},
    )

    inputs = build_usage_inputs(payload)

    assert inputs["users"] == 1000
    assert inputs["api_requests_per_user_per_month"] == 50
    assert inputs["requests_per_month"] == 50_000


def test_build_usage_inputs_preserves_existing_totals():
    payload = GlobalUsageModelPayload(
        llm={},
        static={"users": 500, "requests_per_month": 12_000},
    )

    inputs = build_usage_inputs(payload)

    assert inputs["requests_per_month"] == 12_000


def test_build_usage_inputs_preserves_string_capacity_mode():
    payload = GlobalUsageModelPayload(
        llm={
            "capacity_mode": UsageParameterEstimate(
                value="Serverless",
                reason="Low traffic MVP.",
            ),
            "request_units_per_user_per_month": UsageParameterEstimate(
                value=120,
                reason="Typical document reads and writes.",
            ),
        },
        static={"users": 1000},
    )

    inputs = build_usage_inputs(payload)

    assert inputs["capacity_mode"] == "Serverless"
    assert inputs["request_units_per_month"] == 120_000


def test_build_usage_inputs_preserves_authentication_methods_list():
    payload = GlobalUsageModelPayload(
        llm={},
        static={
            "users": 1000,
            "authentication_methods": ["email", "google", "sms"],
        },
    )

    inputs = build_usage_inputs(payload)

    assert inputs["authentication_methods"] == ["email", "google", "sms"]


def test_build_usage_inputs_defaults_sms_verifications_when_sms_selected():
    payload = GlobalUsageModelPayload(
        llm={
            "sms_verifications_per_user_per_month": UsageParameterEstimate(
                value=0,
                reason="Ignored SMS auth.",
            ),
        },
        static={
            "users": 10_000,
            "authentication_methods": ["email", "sms"],
        },
    )

    inputs = build_usage_inputs(payload)

    assert inputs["sms_verifications_per_user_per_month"] == 1.0


def test_build_usage_inputs_keeps_positive_sms_verifications():
    payload = GlobalUsageModelPayload(
        llm={
            "sms_verifications_per_user_per_month": UsageParameterEstimate(
                value=2.5,
                reason="Frequent SMS sign-in.",
            ),
        },
        static={
            "users": 10_000,
            "authentication_methods": ["sms"],
        },
    )

    inputs = build_usage_inputs(payload)

    assert inputs["sms_verifications_per_user_per_month"] == 2.5


def test_build_usage_inputs_keeps_zero_sms_when_sms_not_selected():
    payload = GlobalUsageModelPayload(
        llm={
            "sms_verifications_per_user_per_month": UsageParameterEstimate(
                value=0,
                reason="No SMS auth.",
            ),
        },
        static={
            "users": 10_000,
            "authentication_methods": ["email", "google"],
        },
    )

    inputs = build_usage_inputs(payload)

    assert inputs["sms_verifications_per_user_per_month"] == 0.0
