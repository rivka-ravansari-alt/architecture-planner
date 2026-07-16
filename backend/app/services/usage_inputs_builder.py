"""Build numeric pricing inputs from a global usage model."""

from __future__ import annotations

from typing import Any

from app.schemas.global_usage_model import GlobalUsageModelPayload, UsageParameterEstimate


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _estimate_value(
    estimate: UsageParameterEstimate | dict[str, Any],
) -> float | str:
    if isinstance(estimate, UsageParameterEstimate):
        if isinstance(estimate.value, str):
            return estimate.value
        return float(estimate.value)
    if isinstance(estimate, dict):
        raw = estimate.get("value")
        if isinstance(raw, str):
            return raw.strip()
        return float(raw or 0)
    return 0.0


def build_usage_inputs(payload: GlobalUsageModelPayload) -> dict[str, Any]:
    """Flatten static + LLM usage values and derive monthly totals."""

    inputs: dict[str, Any] = {}

    for parameter, value in payload.static.items():
        numeric = _coerce_numeric(value)
        if numeric is not None:
            inputs[parameter] = numeric
        else:
            inputs[parameter] = value

    for parameter, estimate in payload.llm.items():
        inputs[parameter] = _estimate_value(estimate)

    users = inputs.get("users")
    if isinstance(users, (int, float)):
        _apply_user_derived_totals(inputs, float(users))

    return inputs


def _apply_user_derived_totals(inputs: dict[str, Any], users: float) -> None:
    """Populate ``*_per_month`` totals from per-user rates when missing."""

    per_user_mappings = (
        ("requests_per_month", "api_requests_per_user_per_month"),
        ("requests_per_month", "requests_per_user_per_month"),
        ("messages_per_month", "messages_per_user_per_month"),
        ("connection_minutes_per_month", "connection_minutes_per_user_per_month"),
        ("reads_per_month", "reads_per_user_per_month"),
        ("writes_per_month", "writes_per_user_per_month"),
        ("request_units_per_month", "request_units_per_user_per_month"),
    )

    for total_key, per_user_key in per_user_mappings:
        if total_key in inputs:
            continue
        per_user = inputs.get(per_user_key)
        if isinstance(per_user, (int, float)):
            inputs[total_key] = users * float(per_user)
