"""Lookup helpers for GCP pricing models."""

from __future__ import annotations

from app.pricing.gcp.definitions import GCP_PRICING_MODELS
from app.pricing.schemas import GcpServicePricingModel

_SERVICE_ALIASES: dict[str, str] = {
    "pub/sub": "Cloud Pub/Sub",
    "cloud pubsub": "Cloud Pub/Sub",
    "memorystore": "Cloud Memorystore for Redis",
    "cloud memorystore": "Cloud Memorystore for Redis",
    "firestore": "Cloud Firestore",
    "gcs": "Cloud Storage",
    "cloud functions": "Cloud Run Functions",
    "functions": "Cloud Run Functions",
    "gemini": "Gemini API",
    "vertex ai search and conversation": "Vertex AI Search",
}

_MODELS_BY_SERVICE: dict[str, GcpServicePricingModel] = {}
for model in GCP_PRICING_MODELS:
    _MODELS_BY_SERVICE[model.service.casefold()] = model
    _MODELS_BY_SERVICE[model.catalog_service_name.casefold()] = model

for alias, canonical in _SERVICE_ALIASES.items():
    canonical_model = _MODELS_BY_SERVICE.get(canonical.casefold())
    if canonical_model is not None:
        _MODELS_BY_SERVICE[alias.casefold()] = canonical_model

_MODELS_BY_COMPONENT_TYPE: dict[str, list[GcpServicePricingModel]] = {}
for model in GCP_PRICING_MODELS:
    for component_type in model.component_types:
        _MODELS_BY_COMPONENT_TYPE.setdefault(component_type, []).append(model)


def normalize_gcp_service_name(service_name: str) -> str:
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


def get_gcp_pricing_model(service_name: str) -> GcpServicePricingModel | None:
    """Return a pricing model by catalog/cloud mapping service name."""
    normalized = normalize_gcp_service_name(service_name)
    return _MODELS_BY_SERVICE.get(normalized.casefold())


def list_gcp_pricing_models_for_component_type(
    component_type: str,
) -> list[GcpServicePricingModel]:
    """Return all GCP pricing models applicable to a component type."""
    return list(_MODELS_BY_COMPONENT_TYPE.get(component_type, []))


def list_gcp_pricing_models() -> list[GcpServicePricingModel]:
    """Return all registered GCP pricing models."""
    return list(GCP_PRICING_MODELS)
