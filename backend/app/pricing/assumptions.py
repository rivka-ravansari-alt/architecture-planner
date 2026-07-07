"""Resolve usage assumptions for a pricing model without calculating prices."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import (
    AssumptionConfidence,
    AssumptionResolutionResult,
    AssumptionSource,
    CloudServicePricingModel,
    MissingAssumption,
    UsageAssumption,
    UsageInputDefinition,
)


def resolve_usage_assumptions(
    model: CloudServicePricingModel,
    *,
    user_provided: dict[str, Any] | None = None,
    inferred: dict[str, UsageAssumption] | None = None,
) -> AssumptionResolutionResult:
    """Merge user, inferred, and default values; surface anything still missing."""
    user_provided = user_provided or {}
    inferred = inferred or {}

    resolved: list[UsageAssumption] = []
    missing: list[MissingAssumption] = []
    resolved_keys: set[str] = set()

    for input_def in model.pricing_model.required_inputs:
        assumption = _resolve_single_input(input_def, user_provided, inferred)
        if assumption is not None:
            resolved.append(assumption)
            resolved_keys.add(input_def.key)
        elif input_def.required:
            missing.append(
                MissingAssumption(
                    key=input_def.key,
                    description=input_def.description,
                    unit=input_def.unit,
                )
            )

    for key, assumption in inferred.items():
        if key in resolved_keys:
            continue
        if any(item.key == key for item in missing):
            continue
        resolved.append(assumption)

    return AssumptionResolutionResult(
        service=model.service,
        resolved=resolved,
        missing=missing,
        ready_for_calculation=len(missing) == 0,
    )


def _resolve_single_input(
    input_def: UsageInputDefinition,
    user_provided: dict[str, Any],
    inferred: dict[str, UsageAssumption],
) -> UsageAssumption | None:
    if input_def.key in user_provided:
        return UsageAssumption(
            key=input_def.key,
            value=coerce_value(user_provided[input_def.key], input_def),
            unit=input_def.unit,
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        )

    if input_def.key in inferred:
        return inferred[input_def.key]

    default = input_def.default_value
    if default is None:
        return None

    return UsageAssumption(
        key=input_def.key,
        value=coerce_value(default, input_def),
        unit=input_def.unit,
        source=AssumptionSource.default,
        confidence=AssumptionConfidence.medium,
    )


def coerce_value(raw: Any, input_def: UsageInputDefinition) -> int | float | str | bool:
    if input_def.data_type.value == "integer":
        return int(raw)
    if input_def.data_type.value == "float":
        return float(raw)
    if input_def.data_type.value == "boolean":
        return bool(raw)
    return str(raw)
