"""Temporary guardrails for implausible per-component costs."""

from __future__ import annotations

import json

from app.config.params import (
    COST_SANITY_COMPONENT_MAX_1000_USERS,
    COST_SANITY_COMPONENT_MAX_100_USERS,
)
from app.services.cost_calculation.audit_serialization import sku_line_to_dict
from app.services.cost_calculation.models import ComponentCostAudit
from app.services.usage_estimation.usage_baseline import parse_active_user_count


def component_cost_threshold(expected_users: str) -> float | None:
    """Return the per-component monthly USD cap for the user tier, or None if uncapped."""
    user_count = parse_active_user_count(expected_users)
    if user_count <= 100:
        return COST_SANITY_COMPONENT_MAX_100_USERS
    if user_count <= 1000:
        return COST_SANITY_COMPONENT_MAX_1000_USERS
    return None


def is_small_user_tier(expected_users: str) -> bool:
    return parse_active_user_count(expected_users) <= 100


def should_exclude_required_component(
    monthly_cost: float,
    *,
    optional: bool,
    expected_users: str,
) -> bool:
    if optional:
        return False
    threshold = component_cost_threshold(expected_users)
    if threshold is None:
        return False
    return monthly_cost > threshold


def format_suspicious_unknown_item(audit: ComponentCostAudit, *, provider: str) -> str:
    threshold = component_cost_threshold(audit.expected_users) or COST_SANITY_COMPONENT_MAX_100_USERS
    payload = {
        "reason": "suspicious_component_cost",
        "provider": provider,
        "component": audit.component_name,
        "component_type": audit.component_type,
        "service": audit.service_name,
        "pricing_model": audit.pricing_model,
        "monthly_cost": round(audit.final_component_cost, 2),
        "expected_users": audit.expected_users,
        "threshold_usd": threshold,
        "sku_audit": [sku_line_to_dict(line) for line in audit.sku_lines],
    }
    return f"suspicious_component_cost: {json.dumps(payload, separators=(',', ':'))}"
