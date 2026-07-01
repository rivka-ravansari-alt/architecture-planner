"""Usage questionnaire answers that drive resource consumption estimates."""

from __future__ import annotations

from dataclasses import dataclass

from app.config.params import (
    USAGE_ESTIMATION_BASE,
    USAGE_PROFILE_AI_REQUESTS_PER_USER_DAY,
    USAGE_PROFILE_BACKGROUND_MULTIPLIER,
    USAGE_PROFILE_FILE_SIZE_GB,
    USAGE_PROFILE_FILES_PER_MONTH,
    USAGE_PROFILE_MAU,
    USAGE_PROFILE_NOTIFICATION_VOLUME,
    USAGE_PROFILE_TOKEN_SIZES,
    USAGE_PROFILE_USER_ACTIVITY,
)
from app.services.usage_estimation.models import ProductCapabilities


def _parse_user_count(expected_users: str) -> int:
    normalized = expected_users.strip().rstrip("+")
    try:
        return max(1, int(normalized))
    except ValueError:
        return 100


@dataclass(frozen=True)
class UsageProfile:
    monthly_active_users: str = "100"
    custom_monthly_active_users: int | None = None
    user_activity: str = "moderate"
    file_uploads_enabled: bool = False
    files_per_month: str = "under_1k"
    average_file_size: str = "small"
    ai_enabled: bool = False
    ai_requests_per_user_per_day: str = "under_1"
    prompt_size: str = "small"
    response_size: str = "medium"
    background_jobs: str = "none"
    notification_channels: tuple[str, ...] = ()
    notifications_per_month: str = "under_1k"

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> UsageProfile | None:
        if not data:
            return None
        channels = data.get("notification_channels") or []
        if not isinstance(channels, list):
            channels = []
        custom = data.get("custom_monthly_active_users")
        custom_value = int(custom) if isinstance(custom, (int, float)) and custom else None
        return cls(
            monthly_active_users=str(data.get("monthly_active_users") or "100"),
            custom_monthly_active_users=custom_value,
            user_activity=str(data.get("user_activity") or "moderate"),
            file_uploads_enabled=bool(data.get("file_uploads_enabled", False)),
            files_per_month=str(data.get("files_per_month") or "under_1k"),
            average_file_size=str(data.get("average_file_size") or "small"),
            ai_enabled=bool(data.get("ai_enabled", False)),
            ai_requests_per_user_per_day=str(
                data.get("ai_requests_per_user_per_day") or "under_1"
            ),
            prompt_size=str(data.get("prompt_size") or "small"),
            response_size=str(data.get("response_size") or "medium"),
            background_jobs=str(data.get("background_jobs") or "none"),
            notification_channels=tuple(str(item) for item in channels),
            notifications_per_month=str(data.get("notifications_per_month") or "under_1k"),
        )

    def resolve_monthly_active_users(self, *, expected_users: str | None = None) -> int:
        if self.monthly_active_users == "custom" and self.custom_monthly_active_users:
            return max(1, self.custom_monthly_active_users)
        if self.monthly_active_users in USAGE_PROFILE_MAU:
            return int(USAGE_PROFILE_MAU[self.monthly_active_users])
        if expected_users:
            return _parse_user_count(expected_users)
        return 100

    def actions_per_user_per_day(self) -> float:
        return USAGE_PROFILE_USER_ACTIVITY.get(self.user_activity, 12.0)

    def estimate_storage_gb(self, *, users: int) -> tuple[float, float]:
        """Derive object and database storage from users, activity, and uploads."""
        base = USAGE_ESTIMATION_BASE
        per_100 = base.get("database_storage_gb_per_100_users", 1.0)

        storage_gb = base["base_storage_gb"]
        database_storage_gb = base["base_database_storage_gb"] + users * (per_100 / 100.0)

        monthly_files = self.monthly_file_uploads()
        file_gb = self.average_file_size_gb()
        if monthly_files > 0:
            storage_gb += monthly_files * file_gb
            database_storage_gb += monthly_files * file_gb * 0.1

        return storage_gb, database_storage_gb

    def monthly_file_uploads(self) -> float:
        if not self.file_uploads_enabled:
            return 0.0
        return USAGE_PROFILE_FILES_PER_MONTH.get(self.files_per_month, 500.0)

    def average_file_size_gb(self) -> float:
        return USAGE_PROFILE_FILE_SIZE_GB.get(self.average_file_size, 0.001)

    def ai_requests_per_user_per_day_value(self) -> float:
        if not self.ai_enabled:
            return 0.0
        return USAGE_PROFILE_AI_REQUESTS_PER_USER_DAY.get(
            self.ai_requests_per_user_per_day,
            0.5,
        )

    def prompt_tokens(self) -> float:
        return USAGE_PROFILE_TOKEN_SIZES.get(self.prompt_size, 250.0)

    def response_tokens(self) -> float:
        return USAGE_PROFILE_TOKEN_SIZES.get(self.response_size, 1000.0)

    def background_multiplier(self) -> float:
        return USAGE_PROFILE_BACKGROUND_MULTIPLIER.get(self.background_jobs, 0.0)

    def monthly_notification_volume(self) -> float:
        if not self.notification_channels:
            return 0.0
        return USAGE_PROFILE_NOTIFICATION_VOLUME.get(self.notifications_per_month, 500.0)

    def to_capabilities(self) -> ProductCapabilities:
        return ProductCapabilities(
            auth=True,
            file_upload=self.file_uploads_enabled,
            background_processing=self.background_jobs != "none",
            dashboards=self.user_activity in {"heavy", "very_heavy", "high", "very_high"},
            ai=self.ai_enabled,
            payments=False,
        )

    @classmethod
    def build_baseline(
        cls,
        *,
        expected_users: str,
        capabilities: ProductCapabilities | None = None,
    ) -> UsageProfile:
        """Conservative defaults when no questionnaire profile was stored."""
        caps = capabilities or ProductCapabilities()
        mau = expected_users if expected_users in USAGE_PROFILE_MAU else "100"
        return cls(
            monthly_active_users=mau,
            user_activity="moderate",
            file_uploads_enabled=caps.file_upload,
            ai_enabled=caps.ai,
            background_jobs="moderate" if caps.background_processing else "none",
            notification_channels=(),
        )
