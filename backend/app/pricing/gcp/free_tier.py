"""Project-level GCP account free-tier pooling."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.pricing.gcp.allowances import (
    POOL_FREE_TIER_ALLOWANCES,
    allowance_key_for_sku,
    pool_id_for_service,
)
from app.pricing.gcp.sku_quantities._helpers import assumptions_by_key, string_value
from app.pricing.schemas import (
    AdjustedSkuQuantityResult,
    GcpServicePricingModel,
    IncludedUsage,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)


@dataclass
class FreeTierPoolState:
    """Mutable account-level free-tier balances shared across components."""

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
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> tuple[bool, str | None]:
    service = model.service
    assumption_map = assumptions_by_key(resolved)

    if service in {"Cloud Memorystore for Redis", "Networking", "Gemini API", "Vertex AI", "Vertex AI Search"}:
        return False, f"{service} has no always-free tier allowances."

    if service == "Cloud Storage":
        storage_class = "standard"
        if "storage_class" in assumption_map:
            storage_class = string_value(assumption_map, "storage_class").strip().casefold()
        if storage_class != "standard":
            return (
                False,
                f"Free tier applies to Standard storage only (storage_class={storage_class!r}).",
            )
        return True, None

    if service == "Cloud SQL":
        instance_tier = "db-f1-micro"
        if "instance_tier" in assumption_map:
            instance_tier = string_value(assumption_map, "instance_tier").strip().casefold()
        if "f1-micro" not in instance_tier and "shared" not in instance_tier:
            return (
                False,
                f"Free tier applies to shared-core tiers only (instance_tier={instance_tier!r}).",
            )
        return True, None

    if service in {
        "Cloud Run Functions",
        "Cloud Run",
        "Cloud Pub/Sub",
        "Cloud Tasks",
        "API Gateway",
        "Secret Manager",
        "Firebase",
        "Firebase Hosting",
        "Cloud Firestore",
        "BigQuery",
        "Cloud Logging",
        "Cloud Monitoring",
        "Cloud Trace",
    }:
        return True, None

    return False, f"No free-tier rules defined for {service!r}."


def apply_project_free_tier(
    model: GcpServicePricingModel,
    raw_result: SkuQuantityResult,
    pool_state: FreeTierPoolState,
    *,
    resolved: list[UsageAssumption],
) -> AdjustedSkuQuantityResult:
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
                                f"GCP Free Tier grant applied to {quantity.sku_key!r}."
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
