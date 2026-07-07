"""Project-level Azure subscription free-tier pooling."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.pricing.azure.allowances import (
    POOL_FREE_TIER_ALLOWANCES,
    allowance_key_for_sku,
    pool_id_for_service,
)
from app.pricing.azure.sku_quantities._helpers import assumptions_by_key, string_value
from app.pricing.schemas import (
    AdjustedSkuQuantityResult,
    AzureServicePricingModel,
    IncludedUsage,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)


@dataclass
class FreeTierPoolState:
    """Mutable subscription-level free-tier balances shared across components."""

    _remaining: dict[str, dict[str, float]] = field(default_factory=dict)
    _initial: dict[str, dict[str, float]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def _ensure_pool(self, pool_id: str) -> None:
        if pool_id in self._remaining:
            return
        allowances = POOL_FREE_TIER_ALLOWANCES.get(pool_id, {})
        self._remaining[pool_id] = dict(allowances)
        self._initial[pool_id] = dict(allowances)

    def remaining(self, pool_id: str, allowance_key: str) -> float:
        self._ensure_pool(pool_id)
        return self._remaining[pool_id].get(allowance_key, 0.0)

    def deduct(self, pool_id: str, allowance_key: str, amount: float) -> float:
        """Deduct up to `amount` from the pool; return the amount actually deducted."""
        if amount <= 0:
            return 0.0
        self._ensure_pool(pool_id)
        pool = self._remaining[pool_id]
        available = pool.get(allowance_key, 0.0)
        deduction = min(amount, available)
        pool[allowance_key] = available - deduction
        if pool[allowance_key] <= 0 and allowance_key in pool:
            pool[allowance_key] = 0.0
        return deduction

    def summary(self) -> dict[str, dict[str, float | dict[str, float]]]:
        summary: dict[str, dict[str, float | dict[str, float]]] = {}
        for pool_id, initial in self._initial.items():
            remaining = self._remaining.get(pool_id, {})
            summary[pool_id] = {
                "initial": dict(initial),
                "remaining": dict(remaining),
                "consumed": {
                    key: initial.get(key, 0.0) - remaining.get(key, 0.0)
                    for key in initial
                },
            }
        return summary


def _is_free_tier_eligible(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> tuple[bool, str | None]:
    service = model.service
    assumption_map = assumptions_by_key(resolved)

    if service == "Azure SQL Database":
        return False, "Azure SQL Database has no subscription free-tier allowances."

    if service == "Azure Container Apps":
        if "min_replicas" not in assumption_map:
            return False, "min_replicas required to determine Container Apps free-tier eligibility."
        min_replicas = int(assumption_map["min_replicas"].value)
        if min_replicas > 0:
            return False, "Free tier applies to consumption plan only (min_replicas=0)."
        return True, None

    if service == "Azure Functions":
        plan = "consumption"
        if "plan" in assumption_map:
            plan = str(assumption_map["plan"].value).strip().casefold()
        elif "plan" in model.pricing_model.default_values:
            plan = str(model.pricing_model.default_values["plan"]).strip().casefold()
        if plan != "consumption":
            return False, f"Free tier applies to consumption plan only (plan={plan!r})."
        return True, None

    if service == "Azure Blob Storage":
        access_tier = string_value(assumption_map, "access_tier").strip().casefold()
        redundancy = string_value(assumption_map, "redundancy").strip().casefold()
        if access_tier != "hot" or redundancy != "lrs":
            return (
                False,
                "Free tier applies to Hot LRS block blob storage only "
                f"(access_tier={access_tier!r}, redundancy={redundancy!r}).",
            )
        return True, None

    if service == "Azure Queue Storage":
        return True, None

    if service == "Azure Service Bus":
        tier = string_value(assumption_map, "messaging_tier").strip().casefold()
        if tier != "standard":
            return False, f"Free tier operations allowance applies to Standard tier only (tier={tier!r})."
        return True, None

    if service in {
        "Azure Cosmos DB",
        "Azure App Center",
        "Notification Hubs",
        "Application Insights",
        "Log Analytics",
        "Azure Monitor",
        "Azure Key Vault",
        "Azure App Configuration",
    }:
        return True, None

    if service in {
        "API Management",
        "Application Gateway",
        "Content Delivery Network",
        "Azure App Service",
        "Azure Redis Cache",
        "Azure Cognitive Search",
        "Azure Foundry Models",
        "Azure Voice Core",
        "Power BI",
    }:
        return False, f"{service} has no subscription free-tier allowances modeled."

    return False, f"No free-tier rules defined for {service!r}."


def apply_project_free_tier(
    model: AzureServicePricingModel,
    raw_result: SkuQuantityResult,
    pool_state: FreeTierPoolState,
    *,
    resolved: list[UsageAssumption],
) -> AdjustedSkuQuantityResult:
    """Apply subscription free-tier deductions to raw SKU quantities."""
    if not raw_result.ready:
        return AdjustedSkuQuantityResult(
            service=raw_result.service,
            quantities=list(raw_result.quantities),
            included_usage=list(raw_result.included_usage),
            missing=list(raw_result.missing),
            ready=False,
        )

    eligible, skip_reason = _is_free_tier_eligible(model, resolved)
    warnings: list[str] = []
    if not eligible and skip_reason:
        warnings.append(skip_reason)

    pool_id = pool_id_for_service(model.service)
    service_allowance_map = model.pricing_model.free_tier.allowances if model.pricing_model.free_tier else {}

    adjusted_quantities: list[SkuQuantity] = []
    included_usage = list(raw_result.included_usage)

    for quantity in raw_result.quantities:
        raw_qty = quantity.raw_quantity if quantity.raw_quantity is not None else quantity.quantity
        billable = quantity.quantity
        deduction = 0.0
        free_tier_applied = False
        qty_warnings = list(quantity.warnings)

        allowance_key = allowance_key_for_sku(model.service, quantity.sku_key)
        if allowance_key is None:
            if eligible and service_allowance_map:
                warnings.append(
                    f"No free-tier allowance mapping for sku_key {quantity.sku_key!r} "
                    f"on {model.service!r}."
                )
        elif eligible and pool_id is not None:
            if allowance_key not in POOL_FREE_TIER_ALLOWANCES.get(pool_id, {}):
                if allowance_key in service_allowance_map:
                    warnings.append(
                        f"Allowance key {allowance_key!r} not in pool {pool_id!r} configuration."
                    )
            else:
                deduction = pool_state.deduct(pool_id, allowance_key, raw_qty)
                billable = max(0.0, raw_qty - deduction)
                free_tier_applied = deduction > 0
                if deduction > 0:
                    included_usage.append(
                        IncludedUsage(
                            sku_key=quantity.sku_key,
                            quantity=deduction,
                            unit=quantity.unit,
                            description=(
                                f"Subscription free-tier grant applied to {quantity.sku_key!r}."
                            ),
                            source="free_tier",
                        )
                    )
                remaining = pool_state.remaining(pool_id, allowance_key)
                if raw_qty > deduction and remaining <= 0:
                    pool_state.warnings.append(
                        f"Free-tier pool {pool_id!r} exhausted for {allowance_key!r}; "
                        f"{billable:,.0f} {quantity.unit} billable on {model.service!r}."
                    )

        adjusted_quantities.append(
            quantity.model_copy(
                update={
                    "raw_quantity": raw_qty,
                    "quantity": billable,
                    "free_tier_deducted": deduction,
                    "free_tier_applied": free_tier_applied,
                    "warnings": qty_warnings,
                }
            )
        )

    warnings.extend(pool_state.warnings)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_warnings: list[str] = []
    for warning in warnings:
        if warning not in seen:
            seen.add(warning)
            unique_warnings.append(warning)

    return AdjustedSkuQuantityResult(
        service=raw_result.service,
        quantities=adjusted_quantities,
        included_usage=included_usage,
        missing=list(raw_result.missing),
        ready=True,
        warnings=unique_warnings,
    )
