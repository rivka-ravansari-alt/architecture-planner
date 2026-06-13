"""Detailed cloud infrastructure cost estimation per category and provider."""

from __future__ import annotations

import math
from typing import Iterable

from app.config.cost_rules import (
    API_GATEWAY_COST_PER_MILLION,
    API_REQUESTS_PER_USER_MONTH,
    AVG_FILE_SIZE_MB,
    COMPONENT_TYPE_TO_INFRA_CATEGORY,
    DASHBOARDS_DATABASE_SURCHARGE,
    ESTIMATED_MONTHLY_USERS,
    FILE_PROCESSING_COMPUTE_SURCHARGE,
    FILES_PER_MONTH_MIDPOINT,
    INFRASTRUCTURE_CATEGORY_BASE,
    INFRASTRUCTURE_CATEGORY_KEYWORDS,
    INFRASTRUCTURE_CATEGORY_ORDER,
    INFRASTRUCTURE_USER_EXPONENT,
    AI_CLOUD_EXCLUDED_KEYWORDS,
    PROVIDER_COST_MULTIPLIER,
    REALTIME_COMPUTE_SURCHARGE,
    STAGE_CLOUD_OVERHEAD,
    STAGE_COMPUTE_MULTIPLIER,
    STAGE_DATABASE_MULTIPLIER,
    STAGE_OBSERVABILITY_MULTIPLIER,
    STORAGE_COST_PER_GB_BY_PROVIDER,
    USER_SCALE_FACTOR,
)
from app.config.params import CLOUD_PROVIDERS
from app.schemas.cost import (
    CloudInfrastructureCostOut,
    CostRange,
    CostRangeOut,
    ProviderCostMatrixOut,
    UsageProfile,
)
from app.schemas.domain import MappedComponent


class CloudInfrastructureCostService:
    def estimate(
        self,
        components: list[MappedComponent],
        usage: UsageProfile,
    ) -> CloudInfrastructureCostOut:
        active = [component for component in components if not component.optional]
        categories: dict[str, ProviderCostMatrixOut] = {}
        provider_totals = {provider: CostRange() for provider in CLOUD_PROVIDERS}

        detected_by_provider = {
            provider: self._detect_categories(active, provider) for provider in CLOUD_PROVIDERS
        }
        all_categories = sorted(
            {category for cats in detected_by_provider.values() for category in cats},
            key=lambda item: (
                INFRASTRUCTURE_CATEGORY_ORDER.index(item)
                if item in INFRASTRUCTURE_CATEGORY_ORDER
                else 99
            ),
        )

        for category in all_categories:
            matrix = ProviderCostMatrixOut()
            for provider in CLOUD_PROVIDERS:
                if category not in detected_by_provider[provider]:
                    continue
                cost = self._estimate_category(provider, category, usage)
                setattr(matrix, provider, CostRangeOut(**cost.to_dict()))
                provider_totals[provider].add(cost.low, cost.high)
            categories[category] = matrix

        for provider in CLOUD_PROVIDERS:
            if not detected_by_provider[provider]:
                continue
            overhead_low, overhead_high = STAGE_CLOUD_OVERHEAD.get(
                usage.stage, STAGE_CLOUD_OVERHEAD["mvp"]
            )
            provider_totals[provider].add(overhead_low, overhead_high)
            multiplier = PROVIDER_COST_MULTIPLIER.get(provider, (1.0, 1.0))
            provider_totals[provider] = CostRange(
                low=provider_totals[provider].low * multiplier[0],
                high=provider_totals[provider].high * multiplier[1],
            ).round_int()

        return CloudInfrastructureCostOut(
            categories=categories,
            provider_totals={
                provider: CostRangeOut(**provider_totals[provider].to_dict())
                for provider in CLOUD_PROVIDERS
            },
        )

    def _detect_categories(
        self,
        components: list[MappedComponent],
        provider: str,
    ) -> set[str]:
        categories: set[str] = set()
        for component in components:
            services = self._valid_services(component.cloud.get(provider, []))
            if not services:
                continue

            for service in services:
                categories.add(self._classify_service(service))

            component_type = component.component_type
            fallback = COMPONENT_TYPE_TO_INFRA_CATEGORY.get(component_type)
            if fallback:
                categories.add(fallback)

        return categories

    def _estimate_category(
        self,
        provider: str,
        category: str,
        usage: UsageProfile,
    ) -> CostRange:
        user_factor = USER_SCALE_FACTOR.get(usage.expected_users, 1.0)
        exponent = INFRASTRUCTURE_USER_EXPONENT.get(category, 0.3)
        scale = math.pow(user_factor, exponent)
        base_low, base_high = INFRASTRUCTURE_CATEGORY_BASE.get(category, (5.0, 20.0))
        total = CostRange(low=base_low * scale, high=base_high * scale)

        if category == "compute":
            total = total.scale(STAGE_COMPUTE_MULTIPLIER.get(usage.stage, 1.0))
            if usage.process_after_upload:
                total.add(*FILE_PROCESSING_COMPUTE_SURCHARGE)
            if usage.real_time:
                total.add(*REALTIME_COMPUTE_SURCHARGE)

        elif category == "database":
            total = total.scale(STAGE_DATABASE_MULTIPLIER.get(usage.stage, 1.0))
            if usage.dashboards:
                total.add(*DASHBOARDS_DATABASE_SURCHARGE)

        elif category == "storage":
            if usage.file_uploads:
                total = CostRange()
                total.add(*self._storage_usage_cost(provider, usage))
            else:
                total = total.scale(0.35)

        elif category == "api_gateway":
            total.add(*self._api_gateway_usage_cost(provider, usage))

        elif category == "cdn" and usage.file_uploads:
            total = total.scale(1.25)

        elif category == "queue" and usage.process_after_upload:
            total = total.scale(1.3)

        elif category in {"monitoring", "logging", "tracing", "alerting"}:
            total = total.scale(STAGE_OBSERVABILITY_MULTIPLIER.get(usage.stage, 1.0))

        elif category == "backups" and usage.stage != "production":
            total = total.scale(0.5)

        return total.round_int()

    @staticmethod
    def _storage_usage_cost(provider: str, usage: UsageProfile) -> tuple[float, float]:
        files = FILES_PER_MONTH_MIDPOINT.get(usage.files_per_month, 500)
        size_mb = AVG_FILE_SIZE_MB.get(usage.average_file_size, 0.5)
        gb_month = max((files * size_mb) / 1024, 0.25)
        per_gb = STORAGE_COST_PER_GB_BY_PROVIDER.get(provider, (0.02, 0.05))
        base_low, base_high = INFRASTRUCTURE_CATEGORY_BASE["storage"]
        return base_low + per_gb[0] * gb_month, base_high + per_gb[1] * gb_month

    @staticmethod
    def _api_gateway_usage_cost(provider: str, usage: UsageProfile) -> tuple[float, float]:
        users = ESTIMATED_MONTHLY_USERS.get(usage.expected_users, 100)
        requests_low = users * API_REQUESTS_PER_USER_MONTH[0]
        requests_high = users * API_REQUESTS_PER_USER_MONTH[1]
        per_million = API_GATEWAY_COST_PER_MILLION.get(provider, (3.5, 5.0))
        return (
            (requests_low / 1_000_000) * per_million[0],
            (requests_high / 1_000_000) * per_million[1],
        )

    @staticmethod
    def _valid_services(services: Iterable[str]) -> list[str]:
        result: list[str] = []
        for service in services:
            normalized = service.strip().lower()
            if not normalized or normalized in {"n/a", "na", "none"}:
                continue
            if CloudInfrastructureCostService._is_ai_api_service(normalized):
                continue
            result.append(normalized)
        return result

    @staticmethod
    def _is_ai_api_service(service: str) -> bool:
        if "ai search" in service:
            return False
        return any(keyword in service for keyword in AI_CLOUD_EXCLUDED_KEYWORDS)

    @staticmethod
    def _classify_service(service: str) -> str:
        for category, keywords in INFRASTRUCTURE_CATEGORY_KEYWORDS:
            if any(keyword in service for keyword in keywords):
                return category
        return "compute"
