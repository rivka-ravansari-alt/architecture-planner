"""Infer pricing model from stored formula metadata."""

from __future__ import annotations

from app.config.params import (
    PRICING_MODEL_COMPUTE_REQUEST,
    PRICING_MODEL_DATABASE_REQUEST,
    PRICING_MODEL_INSTANCE,
    PRICING_MODEL_LINEAR_SKU,
    PRICING_MODEL_MONITORING,
    PRICING_MODEL_NOTIFICATION,
    PRICING_MODEL_STORAGE,
    PRICING_MODEL_TOKEN,
)


def resolve_pricing_model(formula: dict[str, str] | str) -> str:
    if isinstance(formula, str):
        return formula.strip() or PRICING_MODEL_LINEAR_SKU

    if "pricing_model" in formula:
        return str(formula["pricing_model"]).strip()

    combined = " ".join(formula.values()).lower()
    if "monthly_requests" in combined or "monthly_gb_seconds" in combined:
        return PRICING_MODEL_COMPUTE_REQUEST
    if "token" in combined:
        return PRICING_MODEL_TOKEN
    if "notification" in combined or "message" in combined:
        return PRICING_MODEL_NOTIFICATION
    if "metric" in combined or "log_gb" in combined or "log" in combined:
        return PRICING_MODEL_MONITORING
    if "database_requests" in combined:
        return PRICING_MODEL_DATABASE_REQUEST
    if "instance_hours" in combined or "instances" in combined:
        return PRICING_MODEL_INSTANCE
    if "storage_gb" in combined or ".storage." in combined:
        return PRICING_MODEL_STORAGE

    roles = _sku_roles_from_formula(formula)
    if roles == {"storage"} or (len(roles) == 1 and "storage" in roles):
        return PRICING_MODEL_STORAGE

    return PRICING_MODEL_LINEAR_SKU


def _sku_roles_from_formula(formula: dict[str, str]) -> set[str]:
    roles: set[str] = set()
    for expression in formula.values():
        for token in expression.split():
            if token.startswith("skus."):
                role = token.removeprefix("skus.").split(".", 1)[0]
                if role:
                    roles.add(role)
    return roles
