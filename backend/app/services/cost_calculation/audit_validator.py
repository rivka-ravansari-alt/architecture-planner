"""Validation checks for cost calculation audit breakdowns."""

from __future__ import annotations

from app.config.params import (
    COST_SANITY_COMPONENT_MAX_100_USERS,
    COST_SANITY_OPTIONAL_MAX_100_USERS,
    COST_SANITY_REQUIRED_MAX_100_USERS,
    PRICING_MODEL_COMPUTE_REQUEST,
    PRICING_MODEL_DATABASE_REQUEST,
    PRICING_MODEL_STORAGE,
    PRICING_MODEL_TOKEN,
)
from app.services.cost_calculation.models import ComponentCostAudit, ProviderCostResult, SkuLineItem

_PER_MILLION_PATTERNS = ("1m", "million", "1000000", "1,000,000")
_PER_THOUSAND_PATTERNS = ("1k", "thousand", "1000", "1,000")
_SMALL_USER_TIERS = frozenset({"100", "u100"})


def validate_component_audit(audit: ComponentCostAudit) -> list[str]:
    """Run all audit validation checks; return warning strings."""
    warnings: list[str] = []
    warnings.extend(_check_required_sku_roles(audit))
    warnings.extend(_check_unit_mismatches(audit))
    warnings.extend(_check_component_cost_sanity(audit))
    return warnings


def validate_provider_totals(
    result: ProviderCostResult,
    *,
    expected_users: str,
) -> list[str]:
    warnings: list[str] = []
    if expected_users not in _SMALL_USER_TIERS:
        return warnings

    if result.required_total > COST_SANITY_REQUIRED_MAX_100_USERS:
        warnings.append(
            f"{result.provider}: required total ${result.required_total:.2f}/mo is suspiciously high "
            f"for {expected_users} users (threshold ${COST_SANITY_REQUIRED_MAX_100_USERS:.0f})"
        )
    if result.optional_total > COST_SANITY_OPTIONAL_MAX_100_USERS:
        warnings.append(
            f"{result.provider}: optional total ${result.optional_total:.2f}/mo is suspiciously high "
            f"for {expected_users} users (threshold ${COST_SANITY_OPTIONAL_MAX_100_USERS:.0f})"
        )
    return warnings


def _check_required_sku_roles(audit: ComponentCostAudit) -> list[str]:
    required = audit.billable_sku_roles or []
    if not required:
        return []

    present_roles = {line.sku_role for line in audit.sku_lines if line.unit_price is not None}
    warnings: list[str] = []
    for role in required:
        if role not in present_roles:
            warnings.append(
                f"{audit.component_name}: missing required SKU role '{role}' "
                f"for pricing model '{audit.pricing_model}'"
            )
    return warnings


def _check_unit_mismatches(audit: ComponentCostAudit) -> list[str]:
    warnings: list[str] = []
    usage = audit.usage_assumptions

    for line in audit.sku_lines:
        mismatch = _detect_unit_mismatch(line, usage)
        if mismatch:
            warnings.append(f"{audit.component_name}: {mismatch}")
    return warnings


def _detect_unit_mismatch(line: SkuLineItem, usage: dict[str, float]) -> str | None:
    usage_unit = (line.usage_unit or "").casefold()
    if not usage_unit:
        return None

    if any(pattern in usage_unit for pattern in _PER_MILLION_PATTERNS):
        for key in ("monthly_requests", "database_reads", "database_writes", "database_requests"):
            raw = usage.get(key, 0.0)
            if raw > 0 and abs(line.calculated_quantity - raw) < 1.0:
                return (
                    f"SKU '{line.sku_role}' ({line.sku_name or 'unknown'}) usage_unit suggests per-1M pricing "
                    f"but calculated_quantity={line.calculated_quantity:.0f} "
                    f"matches raw {key}={raw:.0f}"
                )

    if any(pattern in usage_unit for pattern in _PER_THOUSAND_PATTERNS):
        for key in ("input_tokens", "output_tokens", "tokens", "metric_samples", "emails_sent", "push_notifications"):
            raw = usage.get(key, 0.0)
            if raw > 0 and abs(line.calculated_quantity - raw) < 1.0:
                return (
                    f"SKU '{line.sku_role}' ({line.sku_name or 'unknown'}) usage_unit suggests per-1K pricing "
                    f"but calculated_quantity={line.calculated_quantity:.0f} "
                    f"matches raw {key}={raw:.0f}"
                )

    return None


def _check_component_cost_sanity(audit: ComponentCostAudit) -> list[str]:
    warnings: list[str] = []
    usage = audit.usage_assumptions
    cost = audit.final_component_cost
    expected_users = audit.expected_users

    if cost < 0:
        warnings.append(f"{audit.component_name}: negative cost ${cost:.2f}")
        return warnings

    if expected_users in _SMALL_USER_TIERS and cost > COST_SANITY_COMPONENT_MAX_100_USERS:
        sku_detail = "; ".join(_format_sku_line(line) for line in audit.sku_lines if line.line_item_cost > 0)
        warnings.append(
            f"{audit.component_name} ({audit.service_name}): component cost ${cost:.2f}/mo exceeds "
            f"${COST_SANITY_COMPONENT_MAX_100_USERS:.0f} for {expected_users} users. SKU audit: {sku_detail}"
        )

    monthly_requests = usage.get("monthly_requests", 0.0)
    component_type = audit.component_type.casefold()
    is_api_like = component_type in {"api", "backend", "web_app", "serverless", "service"} or "api" in component_type

    if is_api_like and monthly_requests > 0 and cost == 0.0 and audit.pricing_model == PRICING_MODEL_COMPUTE_REQUEST:
        warnings.append(
            f"{audit.component_name}: API cost is $0 but monthly_requests={monthly_requests:.0f}"
        )

    reads = usage.get("database_reads", 0.0)
    writes = usage.get("database_writes", 0.0)
    if audit.pricing_model == PRICING_MODEL_DATABASE_REQUEST and (reads + writes) > 0 and cost == 0.0:
        warnings.append(
            f"{audit.component_name}: database cost is $0 but reads={reads:.0f}, writes={writes:.0f}"
        )

    return warnings


def _format_sku_line(line: SkuLineItem) -> str:
    return (
        f"{line.sku_role} ({line.sku_name or line.sku_id or '?'}) "
        f"unit={line.usage_unit or '?'} price={line.unit_price} "
        f"qty={line.calculated_quantity:.4g} cost=${line.line_item_cost:.2f}"
    )
