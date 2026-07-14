"""Project HTTP controller (Step 1 intake + Step 2 component selection)."""

from __future__ import annotations

from app.schemas.auth import UserOut
from app.schemas.component_selection import (
    AddComponentRequest,
    ArchitectureCategoryOut,
    ComponentSelectionResponse,
)
from app.schemas.project import CreateProjectRequest, CreateProjectResponse
from app.services.architecture_component_service import ArchitectureComponentService
from app.services.project_service import ProjectService


class ProjectController:
    def __init__(
        self,
        project_service: ProjectService,
        architecture_component_service: ArchitectureComponentService,
    ) -> None:
        self._service = project_service
        self._architecture_components = architecture_component_service

    def create_project(
        self, payload: CreateProjectRequest, user: UserOut
    ) -> CreateProjectResponse:
        return self._service.create(payload, user)

    def generate_architecture_components(
        self, project_id: str, user: UserOut
    ) -> ComponentSelectionResponse:
        return self._architecture_components.generate(project_id, user)

    def get_architecture_selection(
        self, project_id: str, user: UserOut
    ) -> ComponentSelectionResponse:
        return self._architecture_components.get_selection(project_id, user)

    def list_architecture_categories(
        self, user: UserOut
    ) -> list[ArchitectureCategoryOut]:
        return self._architecture_components.list_categories()

    def add_architecture_component(
        self, project_id: str, payload: AddComponentRequest, user: UserOut
    ) -> ComponentSelectionResponse:
        return self._architecture_components.add_component(
            project_id,
            user,
            payload.selection_id,
            payload.category_id,
            payload.explanation,
        )

    def remove_architecture_component(
        self,
        project_id: str,
        selection_id: str,
        instance_id: str,
        user: UserOut,
    ) -> ComponentSelectionResponse:
        return self._architecture_components.remove_component(
            project_id, user, selection_id, instance_id
        )
