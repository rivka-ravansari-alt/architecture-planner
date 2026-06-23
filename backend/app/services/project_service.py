"""Project business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.params import (
    COMPONENT_SOURCE_AI,
    COMPONENT_TYPE_ALIASES,
    ERR_INVALID_WORKFLOW_STATUS,
    ERR_PROJECT_FORBIDDEN,
    ERR_PROJECT_NOT_FOUND,
    VALID_COMPONENT_SOURCES,
    VALID_COMPONENT_TYPES,
    WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
    WORKFLOW_STATUS_COMPONENTS_APPROVED,
    WORKFLOW_STATUS_COMPONENTS_GENERATED,
    WORKFLOW_STATUS_DIAGRAMS_GENERATED,
    WORKFLOW_STATUS_PRICING_GENERATED,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models import Project, User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import CloudMappingIn, ComponentUpdateIn, ComponentsUpdate, ProjectCreate
from app.services.cloud_defaults_service import CloudDefaultsService


class ProjectService:
    def __init__(
        self,
        db: Session,
        repository: ProjectRepository | None = None,
        cloud_defaults: CloudDefaultsService | None = None,
    ) -> None:
        self._repo = repository or ProjectRepository(db)
        self._cloud_defaults = cloud_defaults or CloudDefaultsService()

    def create(self, payload: ProjectCreate, user: User) -> Project:
        project = self._repo.create(payload, user.id)
        self._repo.commit()
        self._repo.refresh(project)
        return project

    def get_owned_project(self, project_id: str, user: User) -> Project:
        project = self._repo.find_by_id(project_id)
        if project is None:
            raise NotFoundError(ERR_PROJECT_NOT_FOUND)
        if project.user_id != user.id:
            raise ForbiddenError(ERR_PROJECT_FORBIDDEN)
        return project

    def update_components(
        self,
        project_id: str,
        payload: ComponentsUpdate,
        user: User,
    ) -> Project:
        project = self.get_owned_project(project_id, user)
        allowed_statuses = {
            WORKFLOW_STATUS_COMPONENTS_GENERATED,
            WORKFLOW_STATUS_COMPONENTS_APPROVED,
            WORKFLOW_STATUS_DIAGRAMS_GENERATED,
            WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
            WORKFLOW_STATUS_PRICING_GENERATED,
        }
        if project.workflow_status not in allowed_statuses:
            raise BadRequestError(ERR_INVALID_WORKFLOW_STATUS)
        if project.workflow_status in {
            WORKFLOW_STATUS_DIAGRAMS_GENERATED,
            WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
            WORKFLOW_STATUS_PRICING_GENERATED,
        }:
            self._repo.clear_diagrams(project)
            self._repo.clear_pricing(project)
        normalized = self._normalize_component_updates(payload.components)
        self._repo.replace_components(project, normalized)
        self._repo.commit()
        self._repo.refresh(project)
        return project

    def _normalize_component_updates(
        self,
        items: list[ComponentUpdateIn],
    ) -> list[ComponentUpdateIn]:
        normalized: list[ComponentUpdateIn] = []
        for item in items:
            component_type = str(item.type).strip().lower()
            component_type = COMPONENT_TYPE_ALIASES.get(component_type, component_type)
            if component_type not in VALID_COMPONENT_TYPES:
                raise BadRequestError(
                    f"Component '{item.name}' has invalid type '{item.type}'. "
                    f"Choose one of: {', '.join(sorted(VALID_COMPONENT_TYPES))}."
                )

            source = item.source or COMPONENT_SOURCE_AI
            if source not in VALID_COMPONENT_SOURCES:
                raise BadRequestError(
                    f"Component '{item.name}' has invalid source '{item.source}'."
                )

            cloud_mapping = self._resolve_cloud_mapping(item, component_type)
            normalized.append(
                ComponentUpdateIn(
                    key=item.key,
                    name=item.name.strip(),
                    type=component_type,
                    reason=item.reason.strip(),
                    optional=item.optional,
                    source=source,
                    cloud_mapping=cloud_mapping,
                    implementation_options=item.implementation_options,
                )
            )
        return normalized

    def _resolve_cloud_mapping(
        self,
        item: ComponentUpdateIn,
        component_type: str,
    ) -> CloudMappingIn:
        cloud = item.cloud_mapping
        aws = list(cloud.aws) if cloud else []
        gcp = list(cloud.gcp) if cloud else []
        azure = list(cloud.azure) if cloud else []
        if aws or gcp or azure:
            return CloudMappingIn(aws=aws, gcp=gcp, azure=azure)

        defaults = self._cloud_defaults.default_cloud_options_for_type(component_type)
        return CloudMappingIn(
            aws=defaults["aws"],
            gcp=defaults["gcp"],
            azure=defaults["azure"],
        )

    def approve_architecture(self, project_id: str, user: User) -> Project:
        project = self.get_owned_project(project_id, user)
        allowed_statuses = {
            WORKFLOW_STATUS_DIAGRAMS_GENERATED,
            WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
            WORKFLOW_STATUS_PRICING_GENERATED,
        }
        if project.workflow_status not in allowed_statuses:
            raise BadRequestError(ERR_INVALID_WORKFLOW_STATUS)
        self._repo.approve_architecture(project)
        self._repo.commit()
        self._repo.refresh(project)
        return project
