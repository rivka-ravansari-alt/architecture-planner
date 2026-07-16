"""Application-level orchestration for Step 2 (architecture component selection).

Ties together the pipeline without leaking any single responsibility into the
route handler:

    load project -> load categories -> selection service (prompt + OpenAI +
    validation) -> persist to Firestore -> map to API response.
"""

from __future__ import annotations

import logging
from typing import Any

from google.cloud import firestore

from app.config.params import (
    COMPONENT_SELECTION_PROMPT_VERSION,
    ERR_ARCHITECTURE_CATEGORY_NOT_FOUND,
    ERR_COMPONENT_NOT_SELECTED,
    ERR_NO_ARCHITECTURE_CATEGORIES,
    ERR_NO_COMPONENT_SELECTION,
    ERR_PROJECT_FORBIDDEN,
    ERR_PROJECT_NOT_FOUND,
    ERR_SELECTION_NOT_FOUND,
    REASON_COMPONENT_ADDED_BY_USER,
    REASON_COMPONENT_REMOVED_BY_USER,
)
from app.config.settings import settings
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.repositories.architecture_category_repository import (
    ArchitectureCategoryRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import UserOut
from app.schemas.component_selection import (
    ArchitectureCategoryOut,
    ComponentSelectionResponse,
    ComponentSelectionResult,
    ComponentSource,
    SelectedComponentOut,
)
from app.services.architecture_component_selection_service import (
    ArchitectureComponentSelectionService,
)
from app.services.component_selection_mapper import (
    new_component_instance_id,
    to_response,
    to_response_from_lists,
)

logger = logging.getLogger(__name__)


class ArchitectureComponentService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        category_repository: ArchitectureCategoryRepository,
        selection_service: ArchitectureComponentSelectionService,
    ) -> None:
        self._projects = project_repository
        self._categories = category_repository
        self._selection = selection_service

    def generate(self, project_id: str, user: UserOut) -> ComponentSelectionResponse:
        project = self._load_owned_project(project_id, user)
        categories = self._categories.list_all()
        if not categories:
            raise ServiceUnavailableError(ERR_NO_ARCHITECTURE_CATEGORIES)

        normalized_input = self._normalize_input(project)

        # The selection service validates the OpenAI response internally and
        # raises before returning if it is invalid, so reaching this point means
        # the result has passed validation.
        result = self._selection.select(categories=categories, **normalized_input)

        enriched = to_response(result, categories)

        selection_id = self._persist(project_id, result, enriched, normalized_input)
        return self._to_api_response(
            selection_id,
            [item.model_dump(mode="json") for item in enriched.selected],
            [item.model_dump(mode="json") for item in enriched.excluded],
        )

    def get_selection(self, project_id: str, user: UserOut) -> ComponentSelectionResponse:
        """Return the latest saved component selection for review."""

        self._load_owned_project(project_id, user)
        selection = self._load_latest_selection(project_id)
        return self._to_api_response(
            selection["id"],
            selection.get("selected", []),
            selection.get("excluded", []),
        )

    def list_categories(self) -> list[ArchitectureCategoryOut]:
        """Return every architecture category (Firestore is the source of truth)."""

        categories = self._categories.list_all()
        return [
            ArchitectureCategoryOut(
                id=category["id"],
                name=category.get("name", category["id"]),
                description=category.get("description", ""),
                type=category.get("type"),
            )
            for category in categories
        ]

    def add_component(
        self,
        project_id: str,
        user: UserOut,
        selection_id: str,
        category_id: str,
        explanation: str | None,
    ) -> ComponentSelectionResponse:
        """Manually add a component from ``architecture_categories`` to ``selected``.

        The component metadata (``category_id``/``name``/``description``/``type``) is
        taken from the Firestore category; the optional user ``explanation`` is
        stored separately and the source is marked ``user_added``. Each addition
        gets a unique ``instance_id`` so the same category can be added more than
        once.
        """

        self._load_owned_project(project_id, user)
        selection = self._load_selection(project_id, selection_id)
        selected = list(selection.get("selected", []))
        excluded = list(selection.get("excluded", []))

        category = self._categories.find_by_id(category_id)
        if category is None:
            raise BadRequestError(ERR_ARCHITECTURE_CATEGORY_NOT_FOUND)

        new_component = SelectedComponentOut(
            instance_id=new_component_instance_id(),
            category_id=category["id"],
            name=category.get("name", category["id"]),
            description=category.get("description", ""),
            type=category.get("type"),
            reason=explanation or REASON_COMPONENT_ADDED_BY_USER,
            source=ComponentSource.USER_ADDED,
            explanation=explanation,
        )

        selected.append(new_component.model_dump(mode="json"))

        return self._persist_manual_update(project_id, selection["id"], selected, excluded)

    def remove_component(
        self,
        project_id: str,
        user: UserOut,
        selection_id: str,
        instance_id: str,
    ) -> ComponentSelectionResponse:
        """Move a selected component instance into ``excluded`` (removed by the user).

        The target is identified by its unique ``instance_id`` (so duplicates of the
        same ``category_id`` can be removed individually). The component's Firestore
        metadata is preserved; only the reason is set to indicate a user removal.
        The category itself is never deleted.
        """

        self._load_owned_project(project_id, user)
        selection = self._load_selection(project_id, selection_id)
        selected = list(selection.get("selected", []))
        excluded = list(selection.get("excluded", []))

        removed = next(
            (
                item
                for item in selected
                if (item.get("instance_id") or item.get("uid")) == instance_id
            ),
            None,
        )
        if removed is None:
            raise BadRequestError(ERR_COMPONENT_NOT_SELECTED)

        selected = [
            item
            for item in selected
            if (item.get("instance_id") or item.get("uid")) != instance_id
        ]

        removed = {**removed, "reason": REASON_COMPONENT_REMOVED_BY_USER}
        excluded.append(removed)

        return self._persist_manual_update(project_id, selection["id"], selected, excluded)

    def _load_latest_selection(self, project_id: str) -> dict[str, Any]:
        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)
        return selection

    def _load_selection(self, project_id: str, selection_id: str) -> dict[str, Any]:
        selection = self._projects.get_architecture_selection(project_id, selection_id)
        if selection is None:
            raise NotFoundError(ERR_SELECTION_NOT_FOUND)
        return selection

    def _to_api_response(
        self,
        selection_id: str,
        selected: list[Any],
        excluded: list[Any],
    ) -> ComponentSelectionResponse:
        categories = self._categories.list_all()
        enriched = to_response_from_lists(selected, excluded, categories)
        return ComponentSelectionResponse(
            selection_id=selection_id,
            selected=enriched.selected,
            excluded=enriched.excluded,
        )

    def _persist_manual_update(
        self,
        project_id: str,
        selection_id: str,
        selected: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
    ) -> ComponentSelectionResponse:
        self._projects.update_architecture_selection(
            project_id, selection_id, selected, excluded
        )
        response = self._to_api_response(selection_id, selected, excluded)
        logger.info(
            "updated architecture selection project_id=%s selection_id=%s "
            "selected=%d excluded=%d",
            project_id,
            selection_id,
            len(selected),
            len(excluded),
        )
        return response

    def _load_owned_project(self, project_id: str, user: UserOut) -> dict[str, Any]:
        project = self._projects.find_by_id(project_id)
        if project is None:
            raise NotFoundError(ERR_PROJECT_NOT_FOUND)
        if project.get("user_id") != user.id:
            raise ForbiddenError(ERR_PROJECT_FORBIDDEN)
        return project

    @staticmethod
    def _normalize_input(project: dict[str, Any]) -> dict[str, Any]:
        return {
            "application_description": project.get("description", ""),
            "platform": project.get("platform", "web"),
            "stage": project.get("stage", ""),
            "expected_users": int(project.get("expected_users", 0) or 0),
            "requirements": project.get("requirements", {}) or {},
        }

    def _persist(
        self,
        project_id: str,
        result: ComponentSelectionResult,
        response: ComponentSelectionResponse,
        normalized_input: dict[str, Any],
    ) -> str:
        """Persist the complete, validated selection to Firestore.

        Stores both the exact validated model output (``model_output``: id +
        reason) and the enriched, frontend-ready arrays (``selected`` /
        ``excluded``: instance_id + category_id + name + description + type +
        reason), plus the run metadata and the normalized input used to produce it.
        """

        model_name = "static" if settings.use_static_ai_response else settings.openai_model
        document = {
            "selected": [item.model_dump(mode="json") for item in response.selected],
            "excluded": [item.model_dump(mode="json") for item in response.excluded],
            "model_output": result.model_dump(),
            "created_at": firestore.SERVER_TIMESTAMP,
            "prompt_version": COMPONENT_SELECTION_PROMPT_VERSION,
            "model": model_name,
            "input": {
                "application_description": normalized_input["application_description"],
                "platform": normalized_input["platform"],
                "stage": normalized_input["stage"],
                "expected_users": normalized_input["expected_users"],
                "requirements": normalized_input["requirements"],
            },
        }
        selection_id = self._projects.save_architecture_selection(project_id, document)
        self._projects.invalidate_downstream_artifacts(project_id)
        logger.info(
            "saved architecture selection project_id=%s selection_id=%s "
            "selected=%d excluded=%d",
            project_id,
            selection_id,
            len(response.selected),
            len(response.excluded),
        )
        return selection_id
