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


def formula_for_service(service_code: str, sku_roles: list[str]) -> dict[str, str]:
    override = AWS_FORMULAS.get(service_code)
    if override is not None:
        return dict(override)
    return _linear_per_sku_formula(sku_roles)


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
