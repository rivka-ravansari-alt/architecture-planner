"""Project HTTP controller."""

from __future__ import annotations

import logging

from app.core.exceptions import ArchitectureGenerationError
from app.models import User
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectTypeInfo
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
