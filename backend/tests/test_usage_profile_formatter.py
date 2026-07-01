"""Tests for usage profile prompt formatting."""

from __future__ import annotations

from app.services.usage_profile_formatter import format_usage_profile_lines


def test_format_usage_profile_lines_includes_all_sections():
    lines = format_usage_profile_lines(
        {
            "monthly_active_users": "1000",
            "user_activity": "moderate",
            "background_jobs": "low",
            "file_uploads_enabled": True,
            "files_per_month": "1k_10k",
            "average_file_size": "small",
            "ai_enabled": True,
            "ai_requests_per_user_per_day": "1_5",
            "prompt_size": "medium",
            "response_size": "large",
            "notification_channels": ["sms"],
            "notifications_per_month": "1k_10k",
        }
    )

    joined = "\n".join(lines)
    assert "Expected monthly active users: 1,000" in joined
    assert "Average user activity: Moderate (5–20 actions per day)" in joined
    assert "Background tasks: Low" in joined
    assert "File uploads: Yes" in joined
    assert "Artificial intelligence: Yes" in joined
    assert "Notifications: Yes — SMS" in joined


def test_format_usage_profile_custom_users():
    lines = format_usage_profile_lines(
        {
            "monthly_active_users": "custom",
            "custom_monthly_active_users": 2500,
            "user_activity": "light",
            "background_jobs": "none",
        },
        expected_users="2500",
    )

    assert lines[0] == "- Expected monthly active users: 2,500"
