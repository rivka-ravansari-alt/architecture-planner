"""Pydantic models for the architecture component selection step (Step 2).

These cover three concerns:

* ``ComponentDecision`` / ``ComponentSelectionResult`` — strict validation of the
  raw OpenAI output (only ``id`` and ``reason`` are allowed per item).
* ``SelectedComponentOut`` / ``ComponentSelectionResponse`` — the enriched shape
  returned to the frontend (category ``name``/``description``/``type`` attached).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class ComponentSource(str, Enum):
    """Where a selected/excluded component originated.

    ``ai_selected`` — produced by the AI selection step.
    ``user_added`` — manually added by the user during review.
    """

    AI_SELECTED = "ai_selected"
    USER_ADDED = "user_added"


class ComponentDecision(BaseModel):
    """A single selected/excluded decision as returned by the model.

    ``extra="forbid"`` enforces that each item contains only ``id`` and ``reason``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    reason: str

    @field_validator("id", "reason")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()


class ComponentSelectionResult(BaseModel):
    """The validated, model-shaped selection (ids + reasons only)."""

    model_config = ConfigDict(extra="forbid")

    selected: list[ComponentDecision]
    excluded: list[ComponentDecision]


class SelectedComponentOut(BaseModel):
    """An enriched component decision returned to the frontend.

    ``instance_id`` uniquely identifies this card in the project so the same
    ``category_id`` can appear more than once (e.g. two Compute instances).
    ``category_id`` is the Firestore architecture category id used for cloud
    mapping, pricing, and architecture logic. ``source`` distinguishes
    AI-selected components from ones the user added manually. ``explanation``
    holds the optional free-text note a user attaches when adding a component;
    it is stored separately from the ``reason`` line.
    """

    instance_id: str
    category_id: str
    name: str
    description: str
    type: str | None = None
    reason: str
    source: ComponentSource = ComponentSource.AI_SELECTED
    explanation: str | None = None


class ComponentSelectionResponse(BaseModel):
    """The enriched selection returned by the generate / edit endpoints.

    ``selection_id`` identifies the Firestore document being edited so add/remove
    operations target the same selection the UI is displaying (not merely the
    latest document by ``created_at``, which can differ when generate runs twice).
    """

    selection_id: str
    selected: list[SelectedComponentOut]
    excluded: list[SelectedComponentOut]


class ArchitectureCategoryOut(BaseModel):
    """A single architecture category available to add manually.

    Sourced directly from the Firestore ``architecture_categories`` collection.
    """

    id: str
    name: str
    description: str
    type: str | None = None


class AddComponentRequest(BaseModel):
    """Request body for manually adding a component from a Firestore category."""

    model_config = ConfigDict(extra="forbid")

    selection_id: str
    category_id: str
    explanation: str | None = None

    @field_validator("selection_id", "category_id")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("explanation")
    @classmethod
    def _clean_explanation(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
