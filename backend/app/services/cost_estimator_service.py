"""Deterministic monthly cost estimation from Firestore SKU catalogs."""

from __future__ import annotations

import json
from typing import Any

from app.config.params import CLOUD_PROVIDERS, CLOUD_PROVIDER_LABELS, COST_CURRENCY
from app.schemas.domain import (
    ComponentCostEstimate,
    MappedComponent,
    ProviderCost,
    RequirementContext,
)
from app.services.pricing.catalog_lookup import PricingCatalogLookup
from app.services.pricing.component_pricer import ComponentPricer
from app.services.pricing.pricing_profile_repository import PricingProfileRepository


class CostEstimatorService:
    def __init__(
        self,
        *,
        catalog_lookup: PricingCatalogLookup | None = None,
        component_pricer: ComponentPricer | None = None,
        firestore_client: Any | None = None,
        allow_profile_fallback: bool = False,
    ) -> None:
        if catalog_lookup is None:
            catalog_lookup = self._build_catalog_lookup(firestore_client)

        self._catalog_lookup = catalog_lookup
        profile_client = firestore_client
        if profile_client is None:
            try:
                from app.pricing_ingestion.repositories.firestore_provider import (
                    FirestoreClientFactory,
                )

                profile_client = FirestoreClientFactory.create()
            except Exception:
                profile_client = None
        profile_repository = (
            PricingProfileRepository(profile_client) if profile_client is not None else None
        )
        self._pricer = component_pricer or ComponentPricer(
            catalog_lookup=catalog_lookup,
            profile_repository=profile_repository,
            allow_profile_fallback=allow_profile_fallback,
        )

    @staticmethod
    def _build_catalog_lookup(firestore_client: Any | None) -> PricingCatalogLookup:
        try:
            if firestore_client is None:
                from app.pricing_ingestion.repositories.firestore_provider import (
                    FirestoreClientFactory,
                )

                firestore_client = FirestoreClientFactory.create()
            return PricingCatalogLookup.from_firestore_client(firestore_client)
        except Exception:
            return PricingCatalogLookup()

    def estimate(
        self,
        *,
        components: list[MappedComponent] | None = None,
        expected_users: str,
        stage: str,
        file_upload: bool = False,
        ai: bool = False,
        background_processing: bool = False,
        auth: bool = False,
        dashboards: bool = False,
        payments: bool = False,
        requirements: RequirementContext | None = None,
    ) -> list[ProviderCost]:
        req = requirements or RequirementContext(
            auth=auth,
            file_upload=file_upload,
            ai=ai,
            background_processing=background_processing,
            dashboards=dashboards,
            payments=payments,
        )
        component_list = components or []

        return [
            self._estimate_for_provider(
                provider,
                components=component_list,
                expected_users=expected_users,
                stage=stage,
                requirements=req,
            )
            for provider in CLOUD_PROVIDERS
        ]

    def _estimate_for_provider(
        self,
        provider: str,
        *,
        components: list[MappedComponent],
        expected_users: str,
        stage: str,
        requirements: RequirementContext,
    ) -> ProviderCost:
        component_costs: list[ComponentCostEstimate] = []

        for component in components:
            estimate = self._pricer.price_component(
                component=component,
                provider=provider,
                expected_users=expected_users,
                stage=stage,
                requirements=requirements,
            )
            if estimate is not None:
                component_costs.append(estimate)

        monthly_low = round(sum(item.monthly_cost_min for item in component_costs), 2)
        monthly_high = round(sum(item.monthly_cost_max for item in component_costs), 2)

        return ProviderCost(
            provider=provider,
            monthly_low=monthly_low,
            monthly_high=monthly_high,
            currency=COST_CURRENCY,
            notes=self._build_notes(
                provider=provider,
                expected_users=expected_users,
                stage=stage,
                component_costs=component_costs,
            ),
            component_costs=component_costs,
        )

    @staticmethod
    def _build_notes(
        *,
        provider: str,
        expected_users: str,
        stage: str,
        component_costs: list[ComponentCostEstimate],
    ) -> str:
        label = CLOUD_PROVIDER_LABELS[provider]
        summary = (
            f"SKU-based estimate for {label} at ~{expected_users} users ({stage}). "
            f"Covers {len(component_costs)} billable component(s). "
            "Estimate only, not exact billing."
        )
        payload = {
            "summary": summary,
            "component_costs": [
                {
                    "component_name": item.component_name,
                    "component_type": item.component_type,
                    "component_key": item.component_key,
                    "cloud_provider": item.cloud_provider,
                    "cloud_service": item.cloud_service,
                    "optional": item.optional,
                    "matched_skus": [
                        {
                            "role": sku.role,
                            "sku_id": sku.sku_id,
                            "description": sku.description,
                            "usage_unit": sku.usage_unit,
                            "unit_price_usd": sku.unit_price_usd,
                            "quantity": sku.quantity,
                            "free_tier_applied": sku.free_tier_applied,
                            "cost_usd": sku.cost_usd,
                        }
                        for sku in item.matched_skus
                    ],
                    "usage_assumptions": item.usage_assumptions,
                    "monthly_cost_min": item.monthly_cost_min,
                    "monthly_cost_max": item.monthly_cost_max,
                    "calculation_explanation": item.calculation_explanation,
                    "confidence": item.confidence,
                    "missing_data": item.missing_data,
                    "pricing_audit": item.pricing_audit,
                }
                for item in component_costs
            ],
        }
        return json.dumps(payload, separators=(",", ":"))
