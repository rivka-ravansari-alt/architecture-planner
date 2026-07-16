"""Resolve LLM and static usage parameters for Step 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config.params import (
    DERIVED_TOTAL_USAGE_PARAMETERS,
    GLOBAL_LLM_USAGE_PARAMETERS,
    GLOBAL_STATIC_USAGE_PARAMETERS,
)
from app.repositories.cloud_service_mapping_repository import (
    CloudServiceMappingRepository,
)
from app.repositories.pricing_service_repository import PricingServiceRepository


@dataclass(frozen=True)
class ResolvedUsageParameters:
    """Parameter names grouped by how Step 3 obtains their values."""

    llm: list[str]
    static: list[str]
    used_by: dict[str, list[str]] = field(default_factory=dict)


def _category_ids_from_selection(selected: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in selected:
        category_id = item.get("category_id") or item.get("id")
        if not category_id or category_id in seen:
            continue
        seen.add(category_id)
        ordered.append(category_id)
    return ordered


def _service_ids_from_mapping(mapping: dict[str, Any]) -> set[str]:
    service_ids: set[str] = set()
    providers = mapping.get("providers") or {}
    if not isinstance(providers, dict):
        return service_ids

    for provider_services in providers.values():
        if not isinstance(provider_services, list):
            continue
        for entry in provider_services:
            if not isinstance(entry, dict):
                continue
            service_id = entry.get("service_id")
            if isinstance(service_id, str) and service_id.strip():
                service_ids.add(service_id.strip())
    return service_ids


def is_derived_total_usage_parameter(parameter: str) -> bool:
    """Return True when a parameter is a derived monthly total."""

    normalized = parameter.strip()
    if not normalized:
        return True
    if normalized in DERIVED_TOTAL_USAGE_PARAMETERS:
        return True
    if normalized.endswith("_per_month") and "_per_user_" not in normalized:
        return True
    return False


def _llm_parameters_from_to_know(to_know: dict[str, Any]) -> list[str]:
    llm = to_know.get("llm")
    if isinstance(llm, list):
        return [param for param in llm if isinstance(param, str)]
    if isinstance(llm, dict):
        explicit = llm.get("parameters")
        if isinstance(explicit, list):
            return [param for param in explicit if isinstance(param, str)]
    return []


def _static_parameters_from_to_know(to_know: dict[str, Any]) -> list[str]:
    static = to_know.get("static")
    if isinstance(static, list):
        return [param for param in static if isinstance(param, str)]
    return []


class UsageParameterResolver:
    """Determine which usage parameters Step 3 must collect."""

    def __init__(
        self,
        mapping_repository: CloudServiceMappingRepository,
        pricing_repository: PricingServiceRepository,
    ) -> None:
        self._mappings = mapping_repository
        self._pricing = pricing_repository

    def resolve_for_selected_components(
        self, selected_components: list[dict[str, Any]]
    ) -> ResolvedUsageParameters:
        """Return behavioral LLM params and project-backed static params separately."""

        category_ids = _category_ids_from_selection(selected_components)
        service_ids: set[str] = set()

        for category_id in category_ids:
            mapping = self._mappings.find_by_id(category_id)
            if mapping is None:
                continue
            service_ids.update(_service_ids_from_mapping(mapping))

        llm_parameters: set[str] = set(GLOBAL_LLM_USAGE_PARAMETERS)
        static_parameters: set[str] = set(GLOBAL_STATIC_USAGE_PARAMETERS)
        used_by: dict[str, set[str]] = {}

        for service_id in sorted(service_ids):
            pricing_service = self._pricing.find_by_id(service_id)
            if pricing_service is None:
                continue
            to_know = pricing_service.get("to_know") or {}
            if not isinstance(to_know, dict):
                continue

            for param in _llm_parameters_from_to_know(to_know):
                cleaned = param.strip()
                if not cleaned:
                    continue
                used_by.setdefault(cleaned, set()).add(service_id)
                if not is_derived_total_usage_parameter(cleaned):
                    llm_parameters.add(cleaned)

            for param in _static_parameters_from_to_know(to_know):
                cleaned = param.strip()
                if not cleaned:
                    continue
                used_by.setdefault(cleaned, set()).add(service_id)
                if cleaned and cleaned not in DERIVED_TOTAL_USAGE_PARAMETERS:
                    static_parameters.add(cleaned)

        for param in GLOBAL_STATIC_USAGE_PARAMETERS:
            if param not in used_by and service_ids:
                used_by[param] = set(service_ids)

        return ResolvedUsageParameters(
            llm=sorted(llm_parameters),
            static=sorted(static_parameters),
            used_by={parameter: sorted(services) for parameter, services in used_by.items()},
        )
