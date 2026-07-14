"""Maps a validated component selection into enriched, frontend-ready shapes.

Enrichment attaches the category ``name``, ``description`` and (when present)
``type`` from the Firestore categories. No category metadata is hardcoded.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.schemas.component_selection import (
    ComponentSelectionResponse,
    ComponentSelectionResult,
    ComponentSource,
    SelectedComponentOut,
)


def new_component_instance_id() -> str:
    """Return a unique per-instance component id."""

    return uuid4().hex


def _resolve_category_id(item: dict[str, Any]) -> str:
    return item.get("category_id") or item.get("id", "")


def _resolve_instance_id(item: dict[str, Any]) -> str:
    return item.get("instance_id") or item.get("uid") or new_component_instance_id()


def _index_categories(categories: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {category["id"]: category for category in categories}


def _enrich(
    decisions: list[Any], categories_by_id: dict[str, dict[str, Any]]
) -> list[SelectedComponentOut]:
    enriched: list[SelectedComponentOut] = []
    for decision in decisions:
        category = categories_by_id.get(decision.id, {})
        enriched.append(
            SelectedComponentOut(
                instance_id=new_component_instance_id(),
                category_id=decision.id,
                name=category.get("name", decision.id),
                description=category.get("description", ""),
                type=category.get("type"),
                reason=decision.reason,
                source=ComponentSource.AI_SELECTED,
                explanation=None,
            )
        )
    return enriched


def to_response(
    result: ComponentSelectionResult, categories: list[dict[str, Any]]
) -> ComponentSelectionResponse:
    """Build the enriched API response from the validated selection."""

    categories_by_id = _index_categories(categories)
    return ComponentSelectionResponse(
        selection_id="",
        selected=_enrich(result.selected, categories_by_id),
        excluded=_enrich(result.excluded, categories_by_id),
    )


def _enrich_stored(
    items: list[dict[str, Any]], categories_by_id: dict[str, dict[str, Any]]
) -> list[SelectedComponentOut]:
    """Rebuild components from stored dicts, refreshing metadata from Firestore.

    Category ``name``/``description``/``type`` always come from the live
    Firestore category (the single source of truth); the user-owned fields
    (``reason``, ``source``, ``explanation``) are preserved from storage.
    """

    enriched: list[SelectedComponentOut] = []
    for item in items:
        category_id = _resolve_category_id(item)
        category = categories_by_id.get(category_id, {})
        enriched.append(
            SelectedComponentOut(
                instance_id=_resolve_instance_id(item),
                category_id=category_id,
                name=category.get("name", item.get("name", category_id)),
                description=category.get("description", item.get("description", "")),
                type=category.get("type", item.get("type")),
                reason=item.get("reason", ""),
                source=item.get("source", ComponentSource.AI_SELECTED),
                explanation=item.get("explanation"),
            )
        )
    return enriched


def to_response_from_lists(
    selected: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    categories: list[dict[str, Any]],
) -> ComponentSelectionResponse:
    """Build the enriched API response from stored selected/excluded dicts."""

    categories_by_id = _index_categories(categories)
    return ComponentSelectionResponse(
        selection_id="",
        selected=_enrich_stored(selected, categories_by_id),
        excluded=_enrich_stored(excluded, categories_by_id),
    )
