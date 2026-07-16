"""Validation for the global usage model (Step 3) response."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from pydantic import ValidationError

from app.config.params import (
    COSMOS_DB_PROVISIONED_MODES,
    COSMOS_DB_SERVERLESS_MODE,
    ERR_AI_NO_JSON_OBJECT,
    ERR_AI_RESPONSE_EMPTY,
    ERR_GLOBAL_USAGE_MODEL_NOT_JSON,
    STRING_ENUM_USAGE_PARAMETERS,
)
from app.core.exceptions import AIValidationError
from app.schemas.global_usage_model import GlobalUsageModelResult, UsageParameterEstimate

# Cosmos DB mode-specific parameters. Only one side applies for a given capacity_mode.
COSMOS_SERVERLESS_ONLY_PARAMETERS: frozenset[str] = frozenset(
    {
        "request_units_per_user_per_month",
        "request_units_per_month",
    }
)
COSMOS_PROVISIONED_ONLY_PARAMETERS: frozenset[str] = frozenset(
    {
        "required_ru_per_second",
    }
)


def _extract_json(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise AIValidationError(ERR_AI_RESPONSE_EMPTY)

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AIValidationError(ERR_AI_NO_JSON_OBJECT)
    return text[start : end + 1]


def parse_global_usage_model(raw: str) -> GlobalUsageModelResult:
    """Parse raw model text into a strictly-validated global usage result."""

    try:
        payload = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        raise AIValidationError(f"{ERR_GLOBAL_USAGE_MODEL_NOT_JSON} {exc}") from exc

    if not isinstance(payload, dict):
        raise AIValidationError("Global usage model response must be a JSON object.")

    try:
        return GlobalUsageModelResult.model_validate(payload)
    except ValidationError as exc:
        raise AIValidationError(
            f"Global usage model response failed schema validation: {exc}"
        ) from exc


def _capacity_mode_value(result: GlobalUsageModelResult) -> str | None:
    estimate = result.usage.get("capacity_mode")
    if estimate is None:
        return None
    value = estimate.value
    return value if isinstance(value, str) else None


def inapplicable_cosmos_parameters(capacity_mode: str | None) -> frozenset[str]:
    """Return Cosmos parameters that do not apply for the chosen capacity mode."""

    if capacity_mode == COSMOS_DB_SERVERLESS_MODE:
        return COSMOS_PROVISIONED_ONLY_PARAMETERS
    if capacity_mode in COSMOS_DB_PROVISIONED_MODES:
        return COSMOS_SERVERLESS_ONLY_PARAMETERS
    return frozenset()


def required_usage_parameters(
    usage_parameters: Iterable[str],
    *,
    capacity_mode: str | None,
) -> list[str]:
    """Return requested parameters that must be present for the current mode."""

    requested = {
        parameter.strip()
        for parameter in usage_parameters
        if isinstance(parameter, str) and parameter.strip()
    }
    optional = inapplicable_cosmos_parameters(capacity_mode)
    return sorted(requested - optional)


def fill_inapplicable_cosmos_defaults(
    result: GlobalUsageModelResult,
    usage_parameters: Iterable[str],
) -> GlobalUsageModelResult:
    """Fill mode-inapplicable Cosmos params with zeroed defaults when omitted."""

    requested = {
        parameter.strip()
        for parameter in usage_parameters
        if isinstance(parameter, str) and parameter.strip()
    }
    capacity_mode = _capacity_mode_value(result)
    optional = inapplicable_cosmos_parameters(capacity_mode)
    if not optional:
        return result

    usage = dict(result.usage)
    for parameter in sorted(optional & requested):
        if parameter in usage:
            continue
        usage[parameter] = UsageParameterEstimate(
            value=0,
            reason=(
                f"Not applicable for capacity_mode={capacity_mode!r}; "
                "defaulted to 0."
            ),
        )
    return GlobalUsageModelResult(usage=usage)


def validate_against_parameters(
    result: GlobalUsageModelResult, usage_parameters: Iterable[str]
) -> None:
    """Enforce that every required requested parameter appears exactly once."""

    requested = {
        parameter.strip()
        for parameter in usage_parameters
        if isinstance(parameter, str) and parameter.strip()
    }
    if not requested:
        raise AIValidationError("No usage parameters were provided for validation.")

    capacity_mode = _capacity_mode_value(result)
    expected = set(
        required_usage_parameters(requested, capacity_mode=capacity_mode)
    )
    actual = set(result.usage.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - requested)

    if missing:
        raise AIValidationError(
            f"Usage parameters missing from the response: {', '.join(missing)}."
        )
    if extra:
        raise AIValidationError(
            f"Usage response includes unexpected parameters: {', '.join(extra)}."
        )


def validate_parameter_semantics(
    result: GlobalUsageModelResult, usage_parameters: Iterable[str]
) -> None:
    """Validate parameter-specific types and enum values."""

    for parameter in usage_parameters:
        cleaned = parameter.strip()
        if not cleaned or cleaned not in result.usage:
            continue

        estimate = result.usage[cleaned]
        allowed = STRING_ENUM_USAGE_PARAMETERS.get(cleaned)
        if allowed is not None:
            if isinstance(estimate.value, (int, float)):
                raise AIValidationError(
                    f"{cleaned} must be a string enum, not a number."
                )
            if not isinstance(estimate.value, str) or estimate.value not in allowed:
                allowed_values = ", ".join(sorted(allowed))
                raise AIValidationError(
                    f"{cleaned} must be one of: {allowed_values}."
                )
            continue

        if isinstance(estimate.value, str):
            raise AIValidationError(f"{cleaned} must be numeric, not a string.")


def parse_and_validate(
    raw: str, usage_parameters: Iterable[str]
) -> GlobalUsageModelResult:
    """Parse the raw response and validate it against the requested parameters."""

    result = parse_global_usage_model(raw)
    validate_against_parameters(result, usage_parameters)
    validate_parameter_semantics(result, usage_parameters)
    return fill_inapplicable_cosmos_defaults(result, usage_parameters)


__all__ = [
    "parse_global_usage_model",
    "validate_against_parameters",
    "validate_parameter_semantics",
    "parse_and_validate",
    "required_usage_parameters",
    "fill_inapplicable_cosmos_defaults",
    "inapplicable_cosmos_parameters",
]
