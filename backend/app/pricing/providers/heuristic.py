"""Heuristic provider pricing stub until AWS/GCP catalog quantity models exist."""

from __future__ import annotations

from app.config.params import (
    CLOUD_PROVIDER_LABELS,
    COST_BASELINE,
    COST_CURRENCY,
    COST_FEATURE_BANDS,
    COST_PRODUCTION_BAND,
    COST_USER_MULTIPLIER,
    FEATURE_FLAG_KEYS,
    STAGE_PRODUCTION,
)
from app.models import Project
from app.schemas.domain import MappedComponent, ProviderCost
from app.services.component_mapper_service import ComponentMapperService


class HeuristicProviderPricing:
    """Estimate monthly cost bands using feature flags and user multipliers."""

    def __init__(self, mapper: ComponentMapperService | None = None) -> None:
        self._mapper = mapper

    def estimate_provider(
        self,
        provider: str,
        project: Project,
        components: list[MappedComponent],
        *,
        mapper: ComponentMapperService | None = None,
    ) -> ProviderCost:
        """Return a heuristic monthly cost range for one cloud provider."""
        active_mapper = mapper or self._mapper
        if active_mapper is None:
            raise ValueError("ComponentMapperService required for heuristic pricing.")

        flags = active_mapper.feature_flags_from_components(components)
        multiplier = COST_USER_MULTIPLIER.get(project.expected_users, 1.0)
        low, high = COST_BASELINE[provider]

        for feature_key in FEATURE_FLAG_KEYS:
            if flags.get(feature_key):
                band_low, band_high = COST_FEATURE_BANDS[feature_key][provider]
                low += band_low
                high += band_high

        if project.stage == STAGE_PRODUCTION:
            prod_low, prod_high = COST_PRODUCTION_BAND[provider]
            low += prod_low
            high += prod_high

        low = round(low * multiplier)
        high = round(high * multiplier)
        label = CLOUD_PROVIDER_LABELS[provider]

        return ProviderCost(
            provider=provider,
            monthly_low=float(low),
            monthly_high=float(high),
            currency=COST_CURRENCY,
            notes=(
                f"Heuristic estimate for {label} at ~{project.expected_users} users "
                f"({project.stage}). Catalog pricing not yet implemented."
            ),
        )
