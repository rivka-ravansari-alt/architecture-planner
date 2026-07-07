"""Shared helpers for Azure SKU quantity calculators."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import (
    AzureServicePricingModel,
    MissingAssumption,
    SkuQuantity,
    UsageAssumption,
)

MONTHLY_SECONDS = 30 * 24 * 60 * 60


def assumptions_by_key(resolved: list[UsageAssumption]) -> dict[str, UsageAssumption]:
    return {item.key: item for item in resolved}


def collect_missing_required(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
    *,
    keys: list[str],
) -> list[MissingAssumption]:
    available = assumptions_by_key(resolved)
    input_defs = {item.key: item for item in model.pricing_model.required_inputs}
    missing: list[MissingAssumption] = []

    for key in keys:
        if key in available:
            continue
        input_def = input_defs.get(key)
        if input_def is None:
            missing.append(
                MissingAssumption(
                    key=key,
                    description=f"Required input {key!r} for SKU quantity calculation",
                    reason="required for SKU quantity calculation",
                )
            )
            continue
        if not input_def.required:
            continue
        missing.append(
            MissingAssumption(
                key=key,
                description=input_def.description,
                unit=input_def.unit,
                reason="required for SKU quantity calculation",
            )
        )

    return missing


def numeric_value(assumption_map: dict[str, UsageAssumption], key: str) -> int | float:
    value = assumption_map[key].value
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    raise TypeError(f"Expected numeric assumption for {key!r}, got {type(value).__name__}")


def string_value(assumption_map: dict[str, UsageAssumption], key: str) -> str:
    return str(assumption_map[key].value)


def input_values_used(
    assumption_map: dict[str, UsageAssumption],
    keys: list[str],
) -> dict[str, int | float | str | bool]:
    return {key: assumption_map[key].value for key in keys if key in assumption_map}


def make_quantity(
    *,
    sku_key: str,
    quantity: float,
    unit: str,
    formula: str,
    assumption_map: dict[str, UsageAssumption],
    input_keys: list[str],
    raw_quantity: float | None = None,
    notes: list[str] | None = None,
    warnings: list[str] | None = None,
) -> SkuQuantity:
    return SkuQuantity(
        sku_key=sku_key,
        quantity=quantity,
        unit=unit,
        formula=formula,
        input_values_used=input_values_used(assumption_map, input_keys),
        raw_quantity=raw_quantity if raw_quantity is not None else quantity,
        free_tier_applied=False,
        notes=notes or [],
        warnings=warnings or [],
    )


def optional_numeric(
    assumption_map: dict[str, UsageAssumption],
    key: str,
    default: int | float,
) -> int | float:
    if key not in assumption_map:
        return default
    return numeric_value(assumption_map, key)


def default_numeric(
    model: AzureServicePricingModel,
    assumption_map: dict[str, UsageAssumption],
    key: str,
) -> int | float:
    if key in assumption_map:
        return numeric_value(assumption_map, key)
    if key in model.pricing_model.default_values:
        value = model.pricing_model.default_values[key]
        if isinstance(value, (int, float)):
            return value
    input_def = next(
        (item for item in model.pricing_model.required_inputs if item.key == key),
        None,
    )
    if input_def is not None and input_def.default_value is not None:
        if isinstance(input_def.default_value, (int, float)):
            return input_def.default_value
    raise KeyError(key)
