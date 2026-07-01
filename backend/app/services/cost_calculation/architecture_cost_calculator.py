"""Sum component costs from Firestore pricing catalogs."""

from __future__ import annotations

from typing import Any

from app.config.params import (
    CALCULATOR_VERSION_PROFILE_DRIVEN,
    CLOUD_OPTION_SKIP_VALUES,
    CLOUD_PROVIDERS,
    CLOUD_PROVIDER_LABELS,
    COST_CURRENCY,
    COST_ESTIMATE_HIGH_FACTOR,
    COST_ESTIMATE_LOW_FACTOR,
)
from app.pricing_ingestion.models.aws_catalog_ref import aws_option_display_name
from app.pricing_ingestion.models.azure_catalog_ref import azure_option_display_name
from app.schemas.domain import MappedComponent, ProviderCost
from app.services.cost_calculation.audit_serialization import build_pricing_debug_table
from app.services.cost_calculation.audit_validator import validate_component_audit, validate_provider_totals
from app.services.cost_calculation.models import (
    ComponentCostAudit,
    ComponentCostLine,
    ProviderCostResult,
)
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_engine import PricingEngine
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.services.cost_calculation.suspicious_cost_guard import (
    format_suspicious_unknown_item,
    should_exclude_required_component,
)
from app.services.usage_estimation import ProductCapabilities, UsageEstimator
from app.services.usage_estimation.models import ArchitectureUsageEstimate


class ArchitectureCostCalculator:
    """Cost aggregator: usage estimation → pricing engine → provider totals."""

    def __init__(
        self,
        pricing_catalog: PricingCatalogRepository,
        *,
        pricing_profiles: PricingProfileRepository | None = None,
        usage_estimator: UsageEstimator | None = None,
        pricing_engine: PricingEngine | None = None,
    ) -> None:
        self._pricing_catalog = pricing_catalog
        self._pricing_profiles = pricing_profiles
        self._usage_estimator = usage_estimator or UsageEstimator()
        self._pricing_engine = pricing_engine or PricingEngine()

    def calculate(
        self,
        *,
        components: list[MappedComponent],
        expected_users: str,
        stage: str,
        capabilities: ProductCapabilities | dict[str, bool] | None = None,
        usage_profile: dict[str, object] | None = None,
    ) -> list[ProviderCost]:
        usage_estimate = self._usage_estimator.estimate(
            expected_users=expected_users,
            stage=stage,
            components=components,
            capabilities=capabilities,
            usage_profile=usage_profile,
        )
        results = [
            self._calculate_provider(
                provider=provider,
                components=components,
                expected_users=expected_users,
                stage=stage,
                usage_estimate=usage_estimate,
            )
            for provider in CLOUD_PROVIDERS
        ]
        return [
            self._to_provider_cost(
                result,
                expected_users=expected_users,
                stage=stage,
                calculator_version=CALCULATOR_VERSION_PROFILE_DRIVEN,
            )
            for result in results
        ]

    def _calculate_provider(
        self,
        *,
        provider: str,
        components: list[MappedComponent],
        expected_users: str,
        stage: str,
        usage_estimate: ArchitectureUsageEstimate,
    ) -> ProviderCostResult:
        result = ProviderCostResult(
            provider=provider,
            required_total=0.0,
            optional_total=0.0,
            currency=COST_CURRENCY,
            calculator_version=CALCULATOR_VERSION_PROFILE_DRIVEN,
        )
        inclusion_by_key: dict[str, tuple[bool, str | None]] = {}

        for component in components:
            if self._should_skip_component(component):
                continue

            service_name = self._selected_service_name(component, provider)
            if not service_name:
                result.unknown_items.append(
                    f"{component.name} ({provider}): no cloud service selected"
                )
                continue

            record = self._pricing_catalog.get_by_service_name(provider, service_name)
            if record is None:
                result.unknown_items.append(
                    f"{component.name} ({provider}): no pricing catalog for '{service_name}'"
                )
                continue

            if self._pricing_profiles is None:
                result.unknown_items.append(
                    f"{component.name} ({provider}): pricing profiles not configured"
                )
                continue

            profile = self._pricing_profiles.get_by_service_name(provider, service_name)
            if profile is None:
                result.unknown_items.append(
                    f"{component.name} ({provider}): no pricing profile for '{service_name}'"
                )
                continue

            component_usage = usage_estimate.component_consumption.get(component.key)
            if component_usage is None:
                component_usage = usage_estimate.global_consumption
            usage_metrics = component_usage.to_pricing_metrics()

            try:
                calc_result = self._pricing_engine.calculate(
                    record,
                    profile,
                    provider=provider,
                    expected_users=expected_users,
                    stage=stage,
                    usage_metrics=usage_metrics,
                )
            except (KeyError, TypeError, ValueError) as exc:
                result.unknown_items.append(
                    f"{component.name} ({provider}): could not price '{service_name}' ({exc})"
                )
                continue

            if calc_result.unsupported:
                result.unknown_items.append(
                    f"{component.name} ({provider}): unsupported pricing model "
                    f"'{calc_result.pricing_model}' for '{service_name}'"
                )
                result.warnings.extend(calc_result.warnings)
                continue

            monthly_cost = max(0.0, calc_result.monthly_cost)

            audit = ComponentCostAudit(
                component_key=component.key,
                component_name=component.name,
                component_type=component.component_type,
                service_name=service_name,
                pricing_record_id=record.id,
                pricing_record_name=record.name,
                pricing_model=calc_result.pricing_model,
                formula=record.formula,
                expected_users=expected_users,
                usage_assumptions=dict(usage_metrics),
                sku_lines=list(calc_result.sku_lines),
                final_component_cost=0.0 if calc_result.missing_catalog_skus else monthly_cost,
                optional=component.optional,
                pricing_profile_id=profile.id,
                pricing_profile_service=profile.service_name,
                billable_sku_roles=list(calc_result.billable_sku_roles),
                ignored_sku_roles=list(calc_result.ignored_sku_roles),
                calculation_warnings=list(calc_result.warnings),
            )

            if calc_result.missing_catalog_skus:
                result.unknown_items.append(
                    f"{component.name} ({provider}): missing catalog SKU(s) for '{service_name}'"
                )
                result.warnings.extend(calc_result.warnings)
                result.warnings.extend(validate_component_audit(audit))
                inclusion_by_key[component.key] = (False, "missing_catalog_sku")
                result.component_lines.append(
                    ComponentCostLine(
                        component_key=component.key,
                        component_name=component.name,
                        component_type=component.component_type,
                        service_name=service_name,
                        monthly_cost=0.0,
                        optional=component.optional,
                        audit=audit,
                    )
                )
                continue

            result.warnings.extend(calc_result.warnings)
            result.warnings.extend(validate_component_audit(audit))

            excluded = should_exclude_required_component(
                monthly_cost,
                optional=component.optional,
                expected_users=expected_users,
            )
            if excluded:
                inclusion_by_key[component.key] = (False, "suspicious_component_cost")
                result.unknown_items.append(format_suspicious_unknown_item(audit, provider=provider))
                result.warnings.append(
                    f"{component.name} ({provider}): excluded from required total — "
                    f"suspicious cost ${monthly_cost:.2f}/mo for {expected_users} users"
                )
            else:
                inclusion_by_key[component.key] = (True, None)
                if component.optional:
                    result.optional_total += monthly_cost
                else:
                    result.required_total += monthly_cost

            line = ComponentCostLine(
                component_key=component.key,
                component_name=component.name,
                component_type=component.component_type,
                service_name=service_name,
                monthly_cost=monthly_cost,
                optional=component.optional,
                audit=audit,
            )
            result.component_lines.append(line)

        result.warnings.extend(validate_provider_totals(result, expected_users=expected_users))
        result.pricing_debug_table = build_pricing_debug_table(
            provider,
            result.component_lines,
            inclusion_by_key=inclusion_by_key,
        )
        return result

    @staticmethod
    def _should_skip_component(component: MappedComponent) -> bool:
        recommended = str(component.implementation_options.get("recommended", "")).strip().lower()
        if recommended == "external_provider":
            return True
        return component.key == "user"

    @staticmethod
    def _selected_service_name(component: MappedComponent, provider: str) -> str | None:
        options = component.cloud.get(provider, [])
        for option in options:
            name = ArchitectureCostCalculator._resolve_option_name(provider, option)
            if not name:
                continue
            if name.casefold() in CLOUD_OPTION_SKIP_VALUES:
                continue
            return name
        return None

    @staticmethod
    def _resolve_option_name(provider: str, option: Any) -> str:
        if provider == "aws":
            return aws_option_display_name(option)
        if provider == "azure":
            return azure_option_display_name(option)
        return str(option).strip()

    @staticmethod
    def _to_provider_cost(
        result: ProviderCostResult,
        *,
        expected_users: str,
        stage: str,
        calculator_version: str,
    ) -> ProviderCost:
        required_low = round(result.required_total * COST_ESTIMATE_LOW_FACTOR, 2)
        required_high = round(result.required_total * COST_ESTIMATE_HIGH_FACTOR, 2)
        optional_low = round(result.optional_total * COST_ESTIMATE_LOW_FACTOR, 2)
        optional_high = round(result.optional_total * COST_ESTIMATE_HIGH_FACTOR, 2)

        label = CLOUD_PROVIDER_LABELS[result.provider]
        notes_parts = [
            f"Estimated range for {label} at ~{expected_users} users ({stage}) "
            "from usage estimation and Firestore catalog pricing.",
            "Monthly total equals required components only; optional add-ons are separate.",
        ]
        if result.unknown_items:
            notes_parts.append(f"Unknown/excluded: {len(result.unknown_items)} item(s).")
        if result.warnings:
            notes_parts.append(f"Warnings: {len(result.warnings)} item(s).")
        notes_parts.append("Estimate only, not exact billing.")

        component_breakdown = list(result.pricing_debug_table)

        return ProviderCost(
            provider=result.provider,
            monthly_low=required_low,
            monthly_high=required_high,
            currency=result.currency,
            notes=" ".join(notes_parts),
            required_low=required_low,
            required_high=required_high,
            optional_low=optional_low,
            optional_high=optional_high,
            unknown_items=list(result.unknown_items),
            warnings=list(result.warnings),
            component_breakdown=component_breakdown,
            pricing_debug_table=list(result.pricing_debug_table),
            calculator_version=calculator_version,
        )
