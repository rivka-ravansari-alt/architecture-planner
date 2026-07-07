"""Pricing formulas per AWS billing service."""

from __future__ import annotations

_AWS_LAMBDA_SERVICE_CODE = "AWSLambda"

AWS_FORMULAS: dict[str, dict[str, str]] = {
    _AWS_LAMBDA_SERVICE_CODE: {
        "request_cost": "monthly_requests * skus.requests.unit_price_usd",
        "duration_cost": "monthly_gb_seconds * skus.duration.unit_price_usd",
        "total": "request_cost + duration_cost",
    },
}

# Catalog roles that must never appear in default linear formulas.
_EXCLUDED_SKU_ROLES: frozenset[str] = frozenset(
    {
        "use1_appconfig_experimenthours",
    }
)


def formula_for_service(
    service_code: str,
    sku_roles: list[str],
    *,
    catalog_id: str | None = None,
) -> dict[str, str]:
    del catalog_id
    override = AWS_FORMULAS.get(service_code)
    if override is not None:
        return dict(override)
    filtered = _billable_sku_roles(sku_roles)
    return _linear_per_sku_formula(filtered)


def _billable_sku_roles(sku_roles: list[str]) -> list[str]:
    return [
        role
        for role in sku_roles
        if role not in _EXCLUDED_SKU_ROLES and "experimenthour" not in role.casefold()
    ]


def _linear_per_sku_formula(sku_roles: list[str]) -> dict[str, str]:
    if not sku_roles:
        return {"total": "0"}

    formula: dict[str, str] = {}
    cost_terms: list[str] = []
    for role in sku_roles:
        cost_key = f"{role}_cost"
        formula[cost_key] = f"{role} * skus.{role}.unit_price_usd"
        cost_terms.append(cost_key)
    formula["total"] = " + ".join(cost_terms)
    return formula
