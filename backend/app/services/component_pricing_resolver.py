"""Resolve selected architecture components to priced cloud services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.repositories.cloud_service_mapping_repository import (
    CloudServiceMappingRepository,
)
from app.repositories.pricing_service_repository import PricingServiceRepository


@dataclass(frozen=True)
class ComponentServiceResolution:
    """Outcome of mapping one component to a provider's pricing service."""

    service_entry: dict[str, Any] | None
    skip_reason: str | None = None


def resolve_service_for_component(
    *,
    mapping_repository: CloudServiceMappingRepository,
    pricing_repository: PricingServiceRepository,
    category_id: str,
    provider: str,
) -> ComponentServiceResolution:
    mapping = mapping_repository.find_by_id(category_id)
    if mapping is None:
        return ComponentServiceResolution(
            None,
            skip_reason=(
                f"No cloud service mapping exists for category '{category_id}'."
            ),
        )

    providers = mapping.get("providers") or {}
    if not isinstance(providers, dict):
        return ComponentServiceResolution(
            None,
            skip_reason=(
                f"Cloud service mapping for '{category_id}' has an invalid "
                f"providers field."
            ),
        )

    provider_services = providers.get(provider)
    if not isinstance(provider_services, list) or not provider_services:
        return ComponentServiceResolution(
            None,
            skip_reason=(
                f"No {provider.upper()} cloud service is mapped for "
                f"category '{category_id}'."
            ),
        )

    sorted_services = sorted(
        (
            entry
            for entry in provider_services
            if isinstance(entry, dict) and entry.get("service_id")
        ),
        key=lambda entry: int(entry.get("priority", 999)),
    )
    if not sorted_services:
        return ComponentServiceResolution(
            None,
            skip_reason=(
                f"No valid {provider.upper()} service entries are mapped for "
                f"category '{category_id}'."
            ),
        )

    missing_pricing: list[str] = []
    for entry in sorted_services:
        service_id = str(entry["service_id"]).strip()
        if pricing_repository.find_by_id(service_id) is not None:
            return ComponentServiceResolution({**entry, "service_id": service_id})
        missing_pricing.append(service_id)

    return ComponentServiceResolution(
        None,
        skip_reason=(
            f"Mapped {provider.upper()} service(s) "
            f"({', '.join(missing_pricing)}) have no pricing definition yet."
        ),
    )
