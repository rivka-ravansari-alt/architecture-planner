"""Canonical SKU roles per pricing model and catalog role resolution."""

from __future__ import annotations

from app.config.params import (
    PRICING_MODEL_COMPUTE_REQUEST,
    PRICING_MODEL_DATABASE_REQUEST,
    PRICING_MODEL_INSTANCE,
    PRICING_MODEL_MONITORING,
    PRICING_MODEL_NOTIFICATION,
    PRICING_MODEL_STORAGE,
    PRICING_MODEL_TOKEN,
)

# Only these roles may produce a line-item cost for each pricing model.
ALLOWED_SKU_ROLES: dict[str, frozenset[str]] = {
    PRICING_MODEL_COMPUTE_REQUEST: frozenset({"cpu", "memory", "requests"}),
    PRICING_MODEL_STORAGE: frozenset({"storage"}),
    PRICING_MODEL_DATABASE_REQUEST: frozenset({"reads", "writes", "storage"}),
    PRICING_MODEL_TOKEN: frozenset({"input_tokens", "output_tokens"}),
    PRICING_MODEL_NOTIFICATION: frozenset({"email", "sms", "push"}),
    PRICING_MODEL_MONITORING: frozenset({"logs_ingested_gb", "metrics"}),
    PRICING_MODEL_INSTANCE: frozenset({"instance", "hour"}),
}

# Map catalog / ingested SKU role keys to canonical roles.
CATALOG_ROLE_ALIASES: dict[str, str] = {
    "cpu": "cpu",
    "memory": "memory",
    "requests": "requests",
    "request": "requests",
    "storage": "storage",
    "reads": "reads",
    "read": "reads",
    "writes": "writes",
    "write": "writes",
    "input_tokens": "input_tokens",
    "input_token": "input_tokens",
    "output_tokens": "output_tokens",
    "output_token": "output_tokens",
    "email": "email",
    "emails": "email",
    "sms": "sms",
    "push": "push",
    "publish": "push",
    "notification": "push",
    "log": "logs_ingested_gb",
    "logs": "logs_ingested_gb",
    "logs_ingested_gb": "logs_ingested_gb",
    "log_gb": "logs_ingested_gb",
    "metric": "metrics",
    "metrics": "metrics",
    "alarm": "metrics",
    "alarms": "metrics",
    "instance": "instance",
    "hour": "hour",
    "hours": "hour",
    "usage": "instance",
}

SUPPORTED_PRICING_MODELS = frozenset(ALLOWED_SKU_ROLES.keys())


def canonical_role(catalog_role: str) -> str | None:
    normalized = catalog_role.strip().casefold()
    return CATALOG_ROLE_ALIASES.get(normalized)


def is_allowed_role(pricing_model: str, catalog_role: str) -> bool:
    allowed = ALLOWED_SKU_ROLES.get(pricing_model)
    if not allowed:
        return False
    canonical = canonical_role(catalog_role)
    return canonical is not None and canonical in allowed


def resolve_catalog_sku(
    skus: dict[str, dict],
    canonical: str,
) -> tuple[str, dict] | None:
    """Find catalog SKU dict for a canonical role (direct key or alias)."""
    if canonical in skus:
        return canonical, skus[canonical]
    for catalog_role, sku in skus.items():
        if canonical_role(catalog_role) == canonical:
            return catalog_role, sku
    return None


def ignored_catalog_roles(pricing_model: str, skus: dict[str, dict]) -> list[str]:
    """Catalog roles that will not be priced for this model."""
    ignored: list[str] = []
    for catalog_role in skus:
        if not is_allowed_role(pricing_model, catalog_role):
            ignored.append(catalog_role)
    return ignored
