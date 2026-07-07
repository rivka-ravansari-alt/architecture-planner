"""Pricing formulas per GCP billing service."""

from __future__ import annotations

_CLOUD_RUN_SERVICE_ID = "152E-C115-5142"
_API_GATEWAY_CATALOG_ID = "api-gateway"

GCP_FORMULAS: dict[str, dict[str, str]] = {
    _CLOUD_RUN_SERVICE_ID: {
        "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
        "memory_cost": (
            "monthly_requests * avg_request_duration * memory_gib * skus.memory.unit_price_usd"
        ),
        "request_cost": "(monthly_requests / 1000000) * skus.requests.unit_price_usd",
        "total": "cpu_cost + memory_cost + request_cost",
    },
}

GCP_FORMULAS_BY_CATALOG_ID: dict[str, dict[str, str]] = {
    _API_GATEWAY_CATALOG_ID: {
        "requests_cost": "(requests / 1000000) * skus.requests.unit_price_usd",
        "egress_cost": "egress_gb * skus.egress.unit_price_usd",
        "total": "requests_cost + egress_cost",
    },
}


def formula_for_service(
    service_id: str,
    sku_roles: list[str],
    *,
    catalog_id: str | None = None,
) -> dict[str, str]:
    if catalog_id and catalog_id in GCP_FORMULAS_BY_CATALOG_ID:
        return dict(GCP_FORMULAS_BY_CATALOG_ID[catalog_id])
    override = GCP_FORMULAS.get(service_id)
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
