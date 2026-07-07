"""Lookup helpers for Azure pricing models."""

from __future__ import annotations

from app.pricing.azure.definitions import AZURE_PRICING_MODELS
from app.pricing.schemas import AzureServicePricingModel

# Catalog display names → canonical pricing model service key.
_SERVICE_ALIASES: dict[str, str] = {
    "sql database": "Azure SQL Database",
    "blob storage": "Azure Blob Storage",
    "queue storage": "Azure Queue Storage",
    "service bus": "Azure Service Bus",
    "functions": "Azure Functions",
    "redis cache": "Azure Redis Cache",
    "foundry models": "Azure Foundry Models",
    "key vault": "Azure Key Vault",
    "app configuration": "Azure App Configuration",
    "voice core": "Azure Voice Core",
}

_MODELS_BY_SERVICE: dict[str, AzureServicePricingModel] = {}
for model in AZURE_PRICING_MODELS:
    _MODELS_BY_SERVICE[model.service.casefold()] = model
    _MODELS_BY_SERVICE[model.catalog_service_name.casefold()] = model

for alias, canonical in _SERVICE_ALIASES.items():
    canonical_model = _MODELS_BY_SERVICE.get(canonical.casefold())
    if canonical_model is not None:
        _MODELS_BY_SERVICE[alias.casefold()] = canonical_model

_MODELS_BY_COMPONENT_TYPE: dict[str, list[AzureServicePricingModel]] = {}
for model in AZURE_PRICING_MODELS:
    for component_type in model.component_types:
        _MODELS_BY_COMPONENT_TYPE.setdefault(component_type, []).append(model)


def normalize_azure_service_name(service_name: str) -> str:
    """Map catalog display names to canonical pricing model keys."""
    stripped = service_name.strip()
    if not stripped:
        return stripped
    alias = _SERVICE_ALIASES.get(stripped.casefold())
    if alias:
        return alias
    model = _MODELS_BY_SERVICE.get(stripped.casefold())
    if model is not None:
        return model.service
    return stripped


def get_azure_pricing_model(service_name: str) -> AzureServicePricingModel | None:
    """Return a pricing model by catalog/cloud mapping service name."""
    normalized = normalize_azure_service_name(service_name)
    return _MODELS_BY_SERVICE.get(normalized.casefold())


def list_azure_pricing_models_for_component_type(
    component_type: str,
) -> list[AzureServicePricingModel]:
    """Return all Azure pricing models applicable to a component type."""
    return list(_MODELS_BY_COMPONENT_TYPE.get(component_type, []))


def list_azure_pricing_models() -> list[AzureServicePricingModel]:
    """Return all registered Azure pricing models."""
    return list(AZURE_PRICING_MODELS)
