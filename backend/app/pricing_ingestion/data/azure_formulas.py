"""Pricing formulas per Azure billing service."""

from __future__ import annotations

_FUNCTIONS_SERVICE_ID = "DZH319HJX2WX"

AZURE_FORMULAS: dict[str, dict[str, str]] = {
    _FUNCTIONS_SERVICE_ID: {
        "execution_cost": "monthly_executions * skus.execution.unit_price_usd",
        "vcpu_cost": "monthly_vcpu_hours * skus.vcpu.unit_price_usd",
        "memory_cost": "monthly_memory_gib_hours * skus.memory.unit_price_usd",
        "total": "execution_cost + vcpu_cost + memory_cost",
    },
}


def formula_for_service(service_id: str, sku_roles: list[str]) -> dict[str, str]:
    override = AZURE_FORMULAS.get(service_id)
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
