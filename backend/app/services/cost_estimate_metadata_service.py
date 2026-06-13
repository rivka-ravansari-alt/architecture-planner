"""Builds assumptions, unknown items, and confidence for cost estimates."""

from __future__ import annotations

from app.config.cost_rules import (
    AVG_FILE_SIZE_LABELS,
    COST_ESTIMATION_DISCLAIMER,
    EXPECTED_USERS_ASSUMPTION_LABELS,
    FILES_PER_MONTH_LABELS,
    REALTIME_TYPE_LABELS,
)
from app.config.params import STAGE_LABELS
from app.schemas.cost import ConfidenceLevel, UsageProfile
from app.schemas.domain import MappedComponent


class CostEstimateMetadataService:
    def build_assumptions(self, usage: UsageProfile) -> list[str]:
        assumptions: list[str] = []

        user_label = EXPECTED_USERS_ASSUMPTION_LABELS.get(
            usage.expected_users,
            f"{usage.expected_users} users",
        )
        assumptions.append(f"Estimated user scale: {user_label}")

        stage_label = STAGE_LABELS.get(usage.stage, usage.stage)
        assumptions.append(f"Stage: {stage_label}")
        assumptions.append("Cloud costs compare AWS, GCP, and Azure for the same architecture")

        if usage.file_uploads:
            assumptions.append("File uploads enabled")
            assumptions.append(
                "Estimated files per month: "
                f"{FILES_PER_MONTH_LABELS.get(usage.files_per_month, usage.files_per_month)}"
            )
            assumptions.append(
                "Average file size: "
                f"{AVG_FILE_SIZE_LABELS.get(usage.average_file_size, usage.average_file_size)}"
            )
            if usage.process_after_upload:
                assumptions.append("Files processed after upload (adds compute and queue cost)")
        if usage.real_time:
            assumptions.append("Real-time updates enabled (adds compute cost)")
            if usage.real_time_types:
                labels = [REALTIME_TYPE_LABELS.get(item, item) for item in usage.real_time_types]
                assumptions.append(f"Real-time types: {', '.join(labels)}")
        if usage.dashboards:
            assumptions.append("Dashboards enabled (adds database cost)")
        if usage.stage == "production":
            assumptions.append("Production stage increases compute, database, and observability costs")

        return assumptions

    def build_unknown_items(
        self,
        usage: UsageProfile,
        components: list[MappedComponent],
    ) -> list[str]:
        unknown: list[str] = [
            "Data transfer, egress, and regional pricing differences not fully modeled",
        ]

        if usage.ai:
            unknown.append("AI provider costs are rough placeholders only — not included in cloud table")

        if usage.payments:
            unknown.append("Payment provider costs (e.g. Stripe fees) are rough placeholders only")

        if usage.notifications:
            unknown.append("Email/SMS provider costs are rough placeholders only")

        if usage.external_integrations:
            unknown.append("Third-party API usage volume and pricing unknown")

        integration_components = [
            component
            for component in components
            if not component.optional
            and component.component_type in {"external_api", "integration"}
        ]
        if integration_components:
            unknown.append("Custom external integrations are not priced in cloud infrastructure")

        if usage.file_uploads and "files_per_month" not in usage.explicit_fields:
            unknown.append("File upload volume assumed from default band")

        if not usage.has_intake_features:
            unknown.append("Detailed questionnaire answers unavailable; legacy defaults applied")

        return unknown

    def compute_confidence(self, usage: UsageProfile) -> ConfidenceLevel:
        score = 2.0
        max_score = 2.0

        max_score += 3.0
        if usage.has_intake_features:
            score += 3.0

        infra_checks: list[tuple[bool, list[str]]] = [
            (usage.file_uploads, ["files_per_month", "average_file_size"]),
            (usage.real_time, ["real_time_types"]),
        ]
        for enabled, required_fields in infra_checks:
            if not enabled:
                continue
            max_score += float(len(required_fields))
            score += sum(1.0 for name in required_fields if name in usage.explicit_fields)

        if usage.expected_users in {"1000", "10000", "100000+"}:
            score += 1.0
        max_score += 1.0

        ratio = score / max_score
        if ratio >= 0.8:
            return "high"
        if ratio >= 0.5:
            return "medium"
        return "low"

    @staticmethod
    def disclaimer() -> str:
        return COST_ESTIMATION_DISCLAIMER
