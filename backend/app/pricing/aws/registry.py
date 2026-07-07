"""Lookup helpers for AWS pricing models."""

from __future__ import annotations

from app.pricing.aws.definitions import AWS_PRICING_MODELS
from app.pricing.schemas import AwsServicePricingModel

# Display names from architecture mapping → canonical pricing model service key.
_SERVICE_ALIASES: dict[str, str] = {
    "rds postgresql": "RDS",
    "rds mysql": "RDS",
    "amazon rds": "RDS",
}

_MODELS_BY_SERVICE: dict[str, AwsServicePricingModel] = {}
for model in AWS_PRICING_MODELS:
    _MODELS_BY_SERVICE[model.service.casefold()] = model
    _MODELS_BY_SERVICE[model.catalog_service_name.casefold()] = model

for alias, canonical in _SERVICE_ALIASES.items():
    canonical_model = _MODELS_BY_SERVICE.get(canonical.casefold())
    if canonical_model is not None:
        _MODELS_BY_SERVICE[alias.casefold()] = canonical_model

_MODELS_BY_COMPONENT_TYPE: dict[str, list[AwsServicePricingModel]] = {}
for model in AWS_PRICING_MODELS:
    for component_type in model.component_types:
        _MODELS_BY_COMPONENT_TYPE.setdefault(component_type, []).append(model)


def normalize_aws_service_name(service_name: str) -> str:
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


def get_aws_pricing_model(service_name: str) -> AwsServicePricingModel | None:
    """Return a pricing model by catalog/cloud mapping service name."""
    normalized = normalize_aws_service_name(service_name)
    return _MODELS_BY_SERVICE.get(normalized.casefold())


def list_aws_pricing_models_for_component_type(
    component_type: str,
) -> list[AwsServicePricingModel]:
    """Return all AWS pricing models applicable to a component type."""
    return list(_MODELS_BY_COMPONENT_TYPE.get(component_type, []))


def list_aws_pricing_models() -> list[AwsServicePricingModel]:
    """Return all registered AWS pricing models."""
    return list(AWS_PRICING_MODELS)
