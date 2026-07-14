"""Validation for the architecture component selection (Step 2) response.

Turns the raw OpenAI text into a strictly-validated ``ComponentSelectionResult``
and enforces the domain rules against the categories loaded from Firestore:

1. Response must be valid JSON.
2. Must contain ``selected`` and ``excluded`` arrays.
3. Each item may contain only ``id`` and ``reason`` (enforced by Pydantic).
4. Every ``id`` must exist in the loaded categories.
5. No ``id`` may appear more than once.
6. No ``id`` may appear in both ``selected`` and ``excluded``.
7. Every available category must appear exactly once, across both arrays.
8. ``reason`` must be a non-empty string (enforced by Pydantic).

On any failure an ``AIValidationError`` is raised; the caller must not persist.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable

from pydantic import ValidationError

from app.config.params import (
    ERR_AI_NO_JSON_OBJECT,
    ERR_AI_RESPONSE_EMPTY,
    ERR_COMPONENT_SELECTION_NOT_JSON,
)
from app.core.exceptions import AIValidationError
from app.schemas.component_selection import ComponentDecision, ComponentSelectionResult


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


def parse_selection(raw: str) -> ComponentSelectionResult:
    """Parse raw model text into a strictly-validated selection result."""

    try:
        payload = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        raise AIValidationError(f"{ERR_COMPONENT_SELECTION_NOT_JSON} {exc}") from exc

    if not isinstance(payload, dict):
        raise AIValidationError("Component selection response must be a JSON object.")

    try:
        return ComponentSelectionResult.model_validate(payload)
    except ValidationError as exc:
        raise AIValidationError(
            f"Component selection response failed schema validation: {exc}"
        ) from exc


def validate_against_categories(
    result: ComponentSelectionResult, category_ids: Iterable[str]
) -> None:
    """Enforce coverage and uniqueness of ids against the Firestore categories."""

    available = set(category_ids)
    if not available:
        raise AIValidationError("No architecture categories were provided for validation.")

    selected_ids = [item.id for item in result.selected]
    excluded_ids = [item.id for item in result.excluded]
    all_ids = selected_ids + excluded_ids

    unknown = sorted({item_id for item_id in all_ids if item_id not in available})
    if unknown:
        raise AIValidationError(
            f"Selection references unknown category ids: {', '.join(unknown)}."
        )

    duplicates = sorted(
        {item_id for item_id, count in Counter(all_ids).items() if count > 1}
    )
    if duplicates:
        raise AIValidationError(
            f"Category ids appear more than once: {', '.join(duplicates)}."
        )

    overlap = sorted(set(selected_ids) & set(excluded_ids))
    if overlap:
        raise AIValidationError(
            f"Category ids appear in both selected and excluded: {', '.join(overlap)}."
        )

    missing = sorted(available - set(all_ids))
    if missing:
        raise AIValidationError(
            f"Categories were not classified as selected or excluded: {', '.join(missing)}."
        )


def parse_and_validate(
    raw: str, category_ids: Iterable[str]
) -> ComponentSelectionResult:
    """Parse the raw response and validate it against the available categories."""

    result = parse_selection(raw)
    validate_against_categories(result, category_ids)
    return result


__all__ = [
    "ComponentDecision",
    "parse_selection",
    "validate_against_categories",
    "parse_and_validate",
]
