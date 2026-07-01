"""Format usage questionnaire answers for AI component-generation prompts."""

from __future__ import annotations

from app.services.usage_estimation.usage_profile import UsageProfile

_MAU_LABELS: dict[str, str] = {
    "100": "100",
    "1000": "1,000",
    "10000": "10,000",
    "100000+": "100,000+",
}

_USER_ACTIVITY_LABELS: dict[str, str] = {
    "light": "Light (1–5 actions per day)",
    "moderate": "Moderate (5–20 actions per day)",
    "heavy": "Heavy (20–100 actions per day)",
    "very_heavy": "Very Heavy (100+ actions per day)",
    "low": "Light (1–5 actions per day)",
    "medium": "Moderate (5–20 actions per day)",
    "high": "Heavy (20–100 actions per day)",
    "very_high": "Very Heavy (100+ actions per day)",
}

_BACKGROUND_LABELS: dict[str, str] = {
    "none": "None",
    "low": "Low",
    "moderate": "Moderate",
    "heavy": "Heavy",
    "medium": "Moderate",
    "high": "Heavy",
}

_FILES_PER_MONTH_LABELS: dict[str, str] = {
    "under_1k": "Less than 1,000",
    "1k_10k": "1,000–10,000",
    "10k_100k": "10,000–100,000",
    "100k_plus": "More than 100,000",
}

_FILE_SIZE_LABELS: dict[str, str] = {
    "small": "Small (<1 MB)",
    "medium": "Medium (1–10 MB)",
    "large": "Large (>10 MB)",
}

_AI_REQUESTS_LABELS: dict[str, str] = {
    "under_1": "Less than 1",
    "1_5": "1–5",
    "5_20": "5–20",
    "20_plus": "More than 20",
}

_AI_SIZE_LABELS: dict[str, str] = {
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
}

_NOTIFICATION_CHANNEL_LABELS: dict[str, str] = {
    "email": "Email",
    "sms": "SMS",
    "push": "Push notifications",
}

_NOTIFICATION_VOLUME_LABELS: dict[str, str] = {
    "under_1k": "Less than 1,000",
    "1k_10k": "1,000–10,000",
    "10k_100k": "10,000–100,000",
    "100k_plus": "More than 100,000",
}


def _label(mapping: dict[str, str], value: str, *, fallback: str | None = None) -> str:
    return mapping.get(value, fallback or value.replace("_", " ").title())


def _format_mau(profile: UsageProfile, *, expected_users: str | None = None) -> str:
    if profile.monthly_active_users == "custom" and profile.custom_monthly_active_users:
        return f"{profile.custom_monthly_active_users:,}"
    if profile.monthly_active_users in _MAU_LABELS:
        return _MAU_LABELS[profile.monthly_active_users]
    if expected_users:
        try:
            return f"{int(expected_users):,}"
        except ValueError:
            return expected_users
    return _MAU_LABELS["100"]


def format_usage_profile_lines(
    usage_profile: UsageProfile | dict[str, object] | None,
    *,
    expected_users: str | None = None,
) -> list[str]:
    """Return bullet lines describing the usage questionnaire for prompts."""
    profile = (
        usage_profile
        if isinstance(usage_profile, UsageProfile)
        else UsageProfile.from_dict(usage_profile)
    )
    if profile is None:
        return []

    lines = [
        f"- Expected monthly active users: {_format_mau(profile, expected_users=expected_users)}",
        f"- Average user activity: {_label(_USER_ACTIVITY_LABELS, profile.user_activity)}",
        f"- Background tasks: {_label(_BACKGROUND_LABELS, profile.background_jobs)}",
    ]

    if profile.file_uploads_enabled:
        lines.append(
            "- File uploads: Yes — "
            f"{_label(_FILES_PER_MONTH_LABELS, profile.files_per_month)} files/month, "
            f"{_label(_FILE_SIZE_LABELS, profile.average_file_size)} average size"
        )
    else:
        lines.append("- File uploads: No")

    if profile.ai_enabled:
        lines.append(
            "- Artificial intelligence: Yes — "
            f"{_label(_AI_REQUESTS_LABELS, profile.ai_requests_per_user_per_day)} requests per active user per day, "
            f"{_label(_AI_SIZE_LABELS, profile.prompt_size)} prompts, "
            f"{_label(_AI_SIZE_LABELS, profile.response_size)} responses"
        )
    else:
        lines.append("- Artificial intelligence: No")

    if profile.notification_channels:
        channels = ", ".join(
            _label(_NOTIFICATION_CHANNEL_LABELS, channel)
            for channel in profile.notification_channels
        )
        lines.append(
            "- Notifications: Yes — "
            f"{channels}; "
            f"{_label(_NOTIFICATION_VOLUME_LABELS, profile.notifications_per_month)} per month"
        )
    else:
        lines.append("- Notifications: No")

    return lines


def format_usage_profile_section(
    usage_profile: UsageProfile | dict[str, object] | None,
    *,
    expected_users: str | None = None,
) -> str:
    lines = format_usage_profile_lines(usage_profile, expected_users=expected_users)
    if not lines:
        return ""
    guidance = (
        "Use this usage profile to select components that support the expected scale, "
        "traffic patterns, and capabilities (for example: object storage for uploads, "
        "queues/workers for background tasks, AI services for model usage, and notification "
        "delivery for outbound messages)."
    )
    return "\n".join([*lines, "", guidance])
