"""Resolve static usage parameter values from project intake and requirements."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import BadRequestError
from app.schemas.global_usage_model import StaticUsageValue

_FILES_PER_MONTH_MIDPOINTS: dict[str, int] = {
    "<100": 50,
    "100-1000": 550,
    "1000-10000": 5_500,
    "10000-100000": 55_000,
    ">100000": 150_000,
}

_AVERAGE_FILE_SIZE_MB_MIDPOINTS: dict[str, float] = {
    "<1mb": 0.5,
    "1-10mb": 5.5,
    "10-100mb": 55.0,
    ">100mb": 150.0,
    "100kb-1mb": 0.55,
    "100mb-1gb": 550.0,
}

_DEFAULT_RETENTION_MONTHS = 12

_ALLOWED_AUTHENTICATION_METHODS = frozenset(
    {
        "email",
        "google",
        "apple",
        "facebook",
        "github",
        "microsoft",
        "sms",
    }
)


class StaticUsageValueResolver:
    """Map static usage parameter names to values from the project document."""

    def resolve(
        self,
        parameter_names: list[str],
        *,
        expected_users: int,
        stage: str,
        requirements: dict[str, Any],
    ) -> dict[str, StaticUsageValue]:
        values: dict[str, StaticUsageValue] = {}
        missing: list[str] = []

        for parameter in parameter_names:
            value = self._resolve_single(
                parameter,
                expected_users=expected_users,
                stage=stage,
                requirements=requirements,
            )
            if value is None:
                missing.append(parameter)
                continue
            values[parameter] = value

        if missing:
            raise BadRequestError(
                "Could not resolve static usage parameters from the project input: "
                f"{', '.join(sorted(missing))}."
            )
        return values

    def _resolve_single(
        self,
        parameter: str,
        *,
        expected_users: int,
        stage: str,
        requirements: dict[str, Any],
    ) -> StaticUsageValue | None:
        if parameter == "users":
            return expected_users
        if parameter == "stage":
            return stage
        if parameter == "documents_per_month":
            return self._documents_per_month(requirements)
        if parameter == "average_document_size_mb":
            return self._average_document_size_mb(requirements)
        if parameter == "retention_months":
            return _DEFAULT_RETENTION_MONTHS
        if parameter == "notification_channel_count":
            return self._notification_channel_count(requirements)
        if parameter == "authentication_methods":
            return self._authentication_methods(requirements)
        if parameter == "ses_free_tier_active":
            return self._ses_free_tier_active(stage)
        return None

    @staticmethod
    def _file_uploads(requirements: dict[str, Any]) -> dict[str, Any]:
        file_uploads = requirements.get("file_uploads") or {}
        if isinstance(file_uploads, dict):
            return file_uploads
        return {}

    def _documents_per_month(self, requirements: dict[str, Any]) -> int:
        file_uploads = self._file_uploads(requirements)
        if not file_uploads.get("enabled"):
            return 0
        band = file_uploads.get("files_per_month")
        if isinstance(band, str) and band in _FILES_PER_MONTH_MIDPOINTS:
            return _FILES_PER_MONTH_MIDPOINTS[band]
        return 0

    def _average_document_size_mb(self, requirements: dict[str, Any]) -> float:
        file_uploads = self._file_uploads(requirements)
        if not file_uploads.get("enabled"):
            return 0.0
        band = file_uploads.get("average_file_size")
        if isinstance(band, str) and band in _AVERAGE_FILE_SIZE_MB_MIDPOINTS:
            return _AVERAGE_FILE_SIZE_MB_MIDPOINTS[band]
        return 0.0

    @staticmethod
    def _notifications(requirements: dict[str, Any]) -> dict[str, Any]:
        notifications = requirements.get("notifications") or {}
        if isinstance(notifications, dict):
            return notifications
        return {}

    def _notification_channel_count(self, requirements: dict[str, Any]) -> int:
        notifications = self._notifications(requirements)
        if not notifications.get("enabled"):
            return 0
        channels = notifications.get("channels")
        if not isinstance(channels, list):
            return 0
        return len([channel for channel in channels if isinstance(channel, str) and channel])

    @staticmethod
    def _authentication(requirements: dict[str, Any]) -> dict[str, Any]:
        authentication = requirements.get("authentication") or {}
        if isinstance(authentication, dict):
            return authentication
        return {}

    def _authentication_methods(self, requirements: dict[str, Any]) -> list[str]:
        authentication = self._authentication(requirements)
        if not authentication.get("enabled"):
            return []
        methods = authentication.get("authentication_methods")
        if not isinstance(methods, list):
            return []
        return [
            method
            for method in methods
            if isinstance(method, str) and method in _ALLOWED_AUTHENTICATION_METHODS
        ]

    @staticmethod
    def _ses_free_tier_active(stage: str) -> int:
        """SES free tier applies for early-stage accounts (first ~12 months).

        Stored as 0/1 so it fits ``StaticUsageValue`` and ``bool(...)`` in the
        pricing script still works.
        """

        return 1 if str(stage).strip().lower() == "mvp" else 0
