"""Serialize cost audit dataclasses for API / DB JSON."""

from __future__ import annotations

from typing import Any

from app.services.cost_calculation.models import ComponentCostAudit, ComponentCostLine, SkuLineItem


def sku_line_to_dict(line: SkuLineItem) -> dict[str, Any]:
    return {
        "sku_role": line.sku_role,
        "sku_name": line.sku_name,
        "sku_id": line.sku_id,
        "usage_unit": line.usage_unit,
        "unit_price": line.unit_price,
        "usage_metric": line.usage_metric,
        "conversion": line.conversion,
        "calculated_quantity": line.calculated_quantity,
        "quantity_note": line.quantity_note,
        "line_item_cost": round(line.line_item_cost, 6),
    }


def component_audit_to_dict(
    audit: ComponentCostAudit,
    *,
    provider: str,
    included_in_total: bool,
    exclusion_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "component_key": audit.component_key,
        "component_type": audit.component_type,
        "component_name": audit.component_name,
        "status": "optional" if audit.optional else "required",
        "selected_cloud_service": audit.service_name,
        "pricing_record_id": audit.pricing_record_id,
        "pricing_record_name": audit.pricing_record_name,
        "pricing_profile_id": audit.pricing_profile_id,
        "pricing_profile_service": audit.pricing_profile_service,
        "pricing_model": audit.pricing_model,
        "billable_sku_roles": list(audit.billable_sku_roles),
        "ignored_sku_roles": list(audit.ignored_sku_roles),
        "formula": audit.formula,
        "expected_users": audit.expected_users,
        "usage_assumptions": audit.usage_assumptions,
        "sku_lines": [sku_line_to_dict(line) for line in audit.sku_lines],
        "warnings": list(audit.calculation_warnings),
        "component_monthly_cost": round(audit.final_component_cost, 6),
        "final_component_cost": round(audit.final_component_cost, 6),
        "included_in_total": included_in_total,
        "exclusion_reason": exclusion_reason,
        "optional": audit.optional,
    }


def build_pricing_debug_table(
    provider: str,
    component_lines: list[ComponentCostLine],
    *,
    inclusion_by_key: dict[str, tuple[bool, str | None]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in component_lines:
        if line.audit is None:
            continue
        included, reason = inclusion_by_key.get(line.component_key, (True, None))
        rows.append(
            component_audit_to_dict(
                line.audit,
                provider=provider,
                included_in_total=included,
                exclusion_reason=reason,
            )
        )
    return rows
