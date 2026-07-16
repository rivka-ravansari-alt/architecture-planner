"""Execute embedded ``script_calculation`` pricing formulas safely."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Any

from app.schemas.pricing import PricingCalculationDetails, PricingFormulaLine
from app.services.pricing_summary_builder import build_calculation_summary

_SAFE_MODULES: dict[str, Any] = {
    "math": math,
}


def _safe_import(
    name: str,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    fromlist: tuple[str, ...] = (),
    level: int = 0,
) -> Any:
    if name in _SAFE_MODULES:
        return _SAFE_MODULES[name]
    raise ImportError(f"import of {name!r} is not allowed in pricing scripts")


_SAFE_BUILTINS: dict[str, Any] = {
    "__import__": _safe_import,
    "abs": abs,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "next": next,
    "round": round,
    "sum": sum,
    "ValueError": ValueError,
}

_SCRIPT_PARAM_KEYS = frozenset({"inputs", "skus", "free_tier"})
_PRICE_TOTAL_KEYS = frozenset(
    {"estimated_price", "total", "price", "monthly_price", "monthly_total"}
)


class PricingCalculationError(Exception):
    """Raised when a pricing script cannot be executed."""


@dataclass(frozen=True)
class PricingScriptResult:
    """Monthly price plus a debug-friendly calculation breakdown."""

    monthly_price: float
    details: PricingCalculationDetails
    calculation_summary: list[str]


def _is_displayable_value(value: Any) -> bool:
    return isinstance(value, (bool, int, float, str)) or value is None


def _normalize_number(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, float):
        return value
    if value.is_integer():
        return int(value)
    return round(value, 6)


def _humanize_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _to_know_keys(to_know: dict[str, Any] | None) -> set[str]:
    if not to_know:
        return set()
    keys: set[str] = set()
    for group in ("llm", "static"):
        values = to_know.get(group) or []
        if isinstance(values, list):
            keys.update(str(item) for item in values)
    return keys


def _details_from_structured(
    payload: dict[str, Any],
    *,
    free_tier: dict[str, Any],
) -> PricingCalculationDetails:
    monthly_price = round(float(payload["monthly_price"]), 2)
    formula_raw = payload.get("formula_breakdown") or []
    formula_breakdown: list[PricingFormulaLine] = []
    if isinstance(formula_raw, list):
        for entry in formula_raw:
            if not isinstance(entry, dict):
                continue
            label = entry.get("label")
            amount = entry.get("amount")
            if label is None or amount is None:
                continue
            formula_breakdown.append(
                PricingFormulaLine(
                    label=str(label),
                    formula=str(entry.get("formula") or label),
                    amount=round(float(amount), 4),
                )
            )

    return PricingCalculationDetails(
        inputs={
            str(key): _normalize_number(value)
            for key, value in (payload.get("inputs") or {}).items()
            if _is_displayable_value(value)
        },
        derived={
            str(key): _normalize_number(value)
            for key, value in (payload.get("derived") or {}).items()
            if _is_displayable_value(value)
        },
        free_tier={
            str(key): _normalize_number(value)
            for key, value in (payload.get("free_tier") or free_tier or {}).items()
            if _is_displayable_value(value)
        },
        billable={
            str(key): _normalize_number(value)
            for key, value in (payload.get("billable") or {}).items()
            if _is_displayable_value(value)
        },
        formula_breakdown=formula_breakdown,
        monthly_price=monthly_price,
    )


def build_pricing_details(
    *,
    monthly_price: float,
    locals_snapshot: dict[str, Any],
    inputs: dict[str, Any],
    free_tier: dict[str, Any],
    to_know: dict[str, Any] | None = None,
) -> PricingCalculationDetails:
    """Classify script locals into a stable Details payload."""

    input_keys = _to_know_keys(to_know) | {
        key for key, value in inputs.items() if _is_displayable_value(value)
    }

    details_inputs: dict[str, Any] = {}
    derived: dict[str, Any] = {}
    billable: dict[str, Any] = {}
    formula_breakdown: list[PricingFormulaLine] = []

    for key, value in locals_snapshot.items():
        if key in _SCRIPT_PARAM_KEYS or key.startswith("_"):
            continue
        if not _is_displayable_value(value):
            continue

        normalized = _normalize_number(value)

        if key.startswith("billable_"):
            billable[key.removeprefix("billable_")] = normalized
            continue

        if key == "billable" and isinstance(value, (int, float)):
            billable["amount"] = normalized
            continue

        if key.endswith("_cost") and isinstance(value, (int, float)):
            formula_breakdown.append(
                PricingFormulaLine(
                    label=_humanize_key(key[: -len("_cost")]),
                    formula=key,
                    amount=round(float(value), 4),
                )
            )
            continue

        if key in _PRICE_TOTAL_KEYS:
            continue

        if key.startswith("free_"):
            continue

        if key in input_keys:
            details_inputs[key] = normalized
            continue

        derived[key] = normalized

    for key in sorted(input_keys):
        if key in details_inputs:
            continue
        if key in inputs and _is_displayable_value(inputs[key]):
            details_inputs[key] = _normalize_number(inputs[key])

    return PricingCalculationDetails(
        inputs=details_inputs,
        derived=derived,
        free_tier={
            str(key): _normalize_number(value)
            for key, value in free_tier.items()
            if _is_displayable_value(value)
        },
        billable=billable,
        formula_breakdown=formula_breakdown,
        monthly_price=round(float(monthly_price), 2),
    )


def execute_pricing_script(
    script: str,
    *,
    inputs: dict[str, Any],
    skus: list[dict[str, Any]],
    free_tier: dict[str, Any],
    to_know: dict[str, Any] | None = None,
    service_id: str | None = None,
) -> PricingScriptResult:
    """Run a seed ``calculate_price`` function and return price + details."""

    if not script or not script.strip():
        raise PricingCalculationError("Pricing script is empty.")

    script_globals: dict[str, Any] = {
        "__builtins__": _SAFE_BUILTINS,
        "math": math,
    }
    namespace: dict[str, Any] = {}
    try:
        exec(
            script,
            script_globals,
            namespace,
        )
    except Exception as error:
        raise PricingCalculationError(f"Could not compile pricing script: {error}") from error

    calculate_price = namespace.get("calculate_price")
    if not callable(calculate_price):
        raise PricingCalculationError("Pricing script must define calculate_price().")

    captured_locals: dict[str, Any] = {}

    def _tracer(frame: Any, event: str, arg: Any) -> Any:
        if (
            event == "return"
            and frame.f_code.co_name == "calculate_price"
            and frame.f_code.co_filename == "<string>"
        ):
            captured_locals.clear()
            captured_locals.update(frame.f_locals)
        return _tracer

    try:
        sys.settrace(_tracer)
        try:
            result = calculate_price(inputs, skus, free_tier)
        finally:
            sys.settrace(None)
    except Exception as error:
        raise PricingCalculationError(f"Pricing calculation failed: {error}") from error

    if isinstance(result, dict):
        if "monthly_price" not in result:
            raise PricingCalculationError(
                "Pricing calculation dict must include monthly_price."
            )
        try:
            monthly_price = round(float(result["monthly_price"]), 2)
        except (TypeError, ValueError) as error:
            raise PricingCalculationError(
                "Pricing calculation monthly_price must be a number."
            ) from error

        if any(
            key in result
            for key in ("inputs", "derived", "billable", "formula_breakdown")
        ):
            details = _details_from_structured(result, free_tier=free_tier)
        else:
            details = build_pricing_details(
                monthly_price=monthly_price,
                locals_snapshot=captured_locals,
                inputs=inputs,
                free_tier=free_tier,
                to_know=to_know,
            )
        summary = result.get("calculation_summary")
        if not isinstance(summary, list) or not summary:
            summary = build_calculation_summary(
                service_id=service_id,
                locals_snapshot=captured_locals,
                free_tier=free_tier,
                monthly_price=monthly_price,
            )
        else:
            summary = [str(item) for item in summary]
        return PricingScriptResult(
            monthly_price=monthly_price,
            details=details,
            calculation_summary=summary,
        )

    if not isinstance(result, (int, float)):
        raise PricingCalculationError("Pricing calculation must return a number.")

    monthly_price = round(float(result), 2)
    details = build_pricing_details(
        monthly_price=monthly_price,
        locals_snapshot=captured_locals,
        inputs=inputs,
        free_tier=free_tier,
        to_know=to_know,
    )
    summary = build_calculation_summary(
        service_id=service_id,
        locals_snapshot=captured_locals,
        free_tier=free_tier,
        monthly_price=monthly_price,
    )
    return PricingScriptResult(
        monthly_price=monthly_price,
        details=details,
        calculation_summary=summary,
    )
