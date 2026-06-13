"""Builds normalized usage profiles from project questionnaire data."""

from __future__ import annotations

from typing import Any

from app.models import Project
from app.schemas.cost import UsageProfile


class UsageProfileService:
    def from_project(self, project: Project) -> UsageProfile:
        features = self._intake_features(project)
        answers = project.answers
        has_intake = bool(features)
        explicit: set[str] = {"expected_users", "stage"}

        file_uploads = self._feature_enabled(features, "file_uploads", answers, "file_upload")
        files_per_month, files_explicit = self._feature_value(
            features, "file_uploads", "estimated_files_per_month", "under_1k"
        )
        average_file_size, size_explicit = self._feature_value(
            features, "file_uploads", "average_file_size", "small"
        )
        process_after_upload = self._feature_bool(features, "file_uploads", "process_after_upload")
        if not process_after_upload and answers:
            process_after_upload = bool(answers.background_processing)

        ai = self._feature_enabled(features, "ai", answers, "ai")
        ai_types, ai_types_explicit = self._feature_list(features, "ai", "ai_types")
        ai_requests_per_day, ai_requests_explicit = self._feature_value(
            features, "ai", "estimated_ai_requests_per_day", "under_100"
        )

        real_time_types, realtime_types_explicit = self._feature_list(
            features, "real_time", "real_time_types"
        )

        if files_explicit:
            explicit.add("files_per_month")
        if size_explicit:
            explicit.add("average_file_size")
        if self._feature_bool(features, "file_uploads", "process_after_upload"):
            explicit.add("process_after_upload")
        if ai_types_explicit:
            explicit.add("ai_types")
        if ai_requests_explicit:
            explicit.add("ai_requests_per_day")
        if realtime_types_explicit:
            explicit.add("real_time_types")

        for feature_key, legacy_key in (
            ("authentication", "auth"),
            ("file_uploads", "file_upload"),
            ("ai", "ai"),
            ("dashboards", "dashboards"),
            ("payments", "payments"),
            ("notifications", None),
            ("external_integrations", None),
            ("real_time", None),
        ):
            if self._feature_enabled(features, feature_key, answers, legacy_key):
                explicit.add(feature_key)

        return UsageProfile(
            expected_users=project.expected_users or "100",
            stage=project.stage or "mvp",
            file_uploads=file_uploads,
            files_per_month=files_per_month,
            average_file_size=average_file_size,
            process_after_upload=process_after_upload,
            ai=ai,
            ai_types=ai_types,
            ai_requests_per_day=ai_requests_per_day,
            notifications=self._feature_enabled(features, "notifications"),
            payments=self._feature_enabled(features, "payments", answers, "payments"),
            external_integrations=self._feature_enabled(features, "external_integrations"),
            real_time=self._feature_enabled(features, "real_time"),
            real_time_types=real_time_types,
            dashboards=self._feature_enabled(features, "dashboards", answers, "dashboards"),
            authentication=self._feature_enabled(features, "authentication", answers, "auth"),
            has_intake_features=has_intake,
            explicit_fields=frozenset(explicit),
        )

    @staticmethod
    def _intake_features(project: Project) -> dict[str, Any]:
        answers = project.answers
        if answers is None:
            return {}
        raw = getattr(answers, "intake_features", None)
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _feature_enabled(
        features: dict[str, Any],
        feature_key: str,
        answers=None,
        legacy_key: str | None = None,
    ) -> bool:
        feature = features.get(feature_key)
        if isinstance(feature, dict) and "enabled" in feature:
            return bool(feature.get("enabled"))
        if answers is not None and legacy_key:
            return bool(getattr(answers, legacy_key, False))
        return False

    @staticmethod
    def _feature_value(
        features: dict[str, Any],
        feature_key: str,
        field_key: str,
        default: str,
    ) -> tuple[str, bool]:
        feature = features.get(feature_key)
        if not isinstance(feature, dict):
            return default, False
        value = feature.get(field_key)
        if not value:
            return default, False
        return str(value), True

    @staticmethod
    def _feature_bool(features: dict[str, Any], feature_key: str, field_key: str) -> bool:
        feature = features.get(feature_key)
        if not isinstance(feature, dict):
            return False
        return bool(feature.get(field_key))

    @staticmethod
    def _feature_list(
        features: dict[str, Any],
        feature_key: str,
        field_key: str,
    ) -> tuple[list[str], bool]:
        feature = features.get(feature_key)
        if not isinstance(feature, dict):
            return [], False
        value = feature.get(field_key)
        if not isinstance(value, list) or not value:
            return [], False
        return [str(item) for item in value if str(item).strip()], True
