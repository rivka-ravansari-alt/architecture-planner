"""Project HTTP controller."""

from __future__ import annotations

import logging

from app.core.exceptions import ArchitectureGenerationError
from app.models import User
from app.schemas.project import (
    ComponentCatalogOut,
    ComponentsUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectTypeInfo,
)
from app.services.catalog_service import CatalogService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class ProjectController:
    def __init__(
        self,
        project_service: ProjectService,
        generation_service: GenerationService,
        catalog_service: CatalogService,
    ) -> None:
        self._projects = project_service
        self._generation = generation_service
        self._catalog = catalog_service

    def list_project_types(self) -> list[ProjectTypeInfo]:
        return self._catalog.list_project_types()

    def list_component_catalog(self) -> list[ComponentCatalogOut]:
        return self._catalog.list_component_catalog()

    def create_project(self, payload: ProjectCreate, user: User) -> ProjectDetail:
        project = self._projects.create(payload, user)
        return ProjectDetail.model_validate(project)

    def generate_project(self, project_id: str, user: User) -> ProjectDetail:
        project = self._projects.get_owned_project(project_id, user)
        logger.info(
            "generate endpoint step=started status=started project_id=%s user_id=%s",
            project_id,
            user.id,
        )
        try:
            result = self._generation.generate(project)
        except ArchitectureGenerationError:
            logger.error(
                "generate endpoint step=failed status=failed project_id=%s",
                project_id,
            )
            raise
        logger.info(
            "generate endpoint step=complete status=completed project_id=%s",
            project_id,
        )
        return ProjectDetail.model_validate(result)

    def generate_components(self, project_id: str, user: User) -> ProjectDetail:
        project = self._projects.get_owned_project(project_id, user)
        try:
            result = self._generation.generate_components(project)
        except ArchitectureGenerationError:
            raise
        return ProjectDetail.model_validate(result)

    def update_components(
        self,
        project_id: str,
        payload: ComponentsUpdate,
        user: User,
    ) -> ProjectDetail:
        project = self._projects.update_components(project_id, payload, user)
        return ProjectDetail.model_validate(project)

    def generate_diagrams(self, project_id: str, user: User) -> ProjectDetail:
        project = self._projects.get_owned_project(project_id, user)
        try:
            result = self._generation.generate_diagrams(project)
        except ArchitectureGenerationError:
            raise
        return ProjectDetail.model_validate(result)

    def approve_architecture(self, project_id: str, user: User) -> ProjectDetail:
        project = self._projects.approve_architecture(project_id, user)
        return ProjectDetail.model_validate(project)

    def generate_pricing(self, project_id: str, user: User) -> ProjectDetail:
        project = self._projects.get_owned_project(project_id, user)
        try:
            result = self._generation.generate_pricing(project)
        except ArchitectureGenerationError:
            raise
        return ProjectDetail.model_validate(result)
