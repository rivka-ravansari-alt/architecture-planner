"""Tests for the global usage model prompt builder (Step 3)."""

from __future__ import annotations

from app.services.global_usage_prompt_builder import GlobalUsagePromptBuilder


def test_build_injects_application_and_parameter_context():
    builder = GlobalUsagePromptBuilder()
    prompt = builder.build(
        application_description="A team task manager.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={"authentication": {"enabled": True}},
        selected_components=[
            {
                "category_id": "compute",
                "name": "Compute",
                "description": "Runs application code.",
                "reason": "Needed for APIs.",
            }
        ],
        usage_parameters=["api_requests_per_user_per_month", "requests_per_user_per_month"],
    )

    assert "A team task manager." in prompt
    assert "Platform:" in prompt
    assert "Web" in prompt
    assert "mvp" in prompt
    assert "1000" in prompt
    assert '"authentication"' in prompt
    assert "category_id" not in prompt
    assert "id: compute" in prompt
    assert "- users" not in prompt
    assert "- requests_per_month" not in prompt
    assert "- api_requests_per_user_per_month" in prompt
    assert "- requests_per_user_per_month" in prompt
    assert "Do not calculate cloud prices." in prompt


def test_build_includes_notification_usage_parameter_guidance():
    builder = GlobalUsagePromptBuilder()
    prompt = builder.build(
        application_description="An ecommerce app.",
        platform="mobile",
        stage="mvp",
        expected_users=5000,
        requirements={
            "notifications": {
                "enabled": True,
                "channels": ["email", "push", "sms"],
            }
        },
        selected_components=[
            {
                "category_id": "notification",
                "name": "Notification Service",
                "description": "Delivers notifications.",
                "reason": "Order and marketing alerts.",
            }
        ],
        usage_parameters=["notifications_per_user_per_month"],
    )

    assert '"notifications"' in prompt
    assert '"channels"' in prompt
    assert "- notifications_per_user_per_month:" in prompt
    assert "enabled channels" in prompt


def test_build_includes_static_usage_values_and_sms_guidance():
    builder = GlobalUsagePromptBuilder()
    prompt = builder.build(
        application_description="A mobile app with SMS login.",
        platform="mobile",
        stage="mvp",
        expected_users=10_000,
        requirements={
            "authentication": {
                "enabled": True,
                "authentication_methods": ["email", "sms"],
            }
        },
        selected_components=[
            {
                "category_id": "authentication",
                "name": "Authentication",
                "description": "User identity.",
                "reason": "Login required.",
            }
        ],
        usage_parameters=["sms_verifications_per_user_per_month"],
        static_usage_values={
            "users": 10_000,
            "authentication_methods": ["email", "sms"],
        },
    )

    assert "Known static inputs" in prompt
    assert '"authentication_methods"' in prompt
    assert '"sms"' in prompt
    assert "- sms_verifications_per_user_per_month:" in prompt
    assert "MUST return a positive number" in prompt


def test_build_includes_workload_type_parameter_guidance():
    builder = GlobalUsagePromptBuilder()
    prompt = builder.build(
        application_description="A team task manager.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={},
        selected_components=[
            {
                "category_id": "compute",
                "name": "Compute",
                "description": "Runs application code.",
                "reason": "Needed for APIs.",
            }
        ],
        usage_parameters=["workload_type", "vcpu"],
    )

    assert "- workload_type:" in prompt
    assert "Burstable" in prompt
    assert "Do not return a number." in prompt
