"""Ensure persisted cost estimates use the current profile-driven calculator."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config.params import (
    CALCULATOR_VERSION_PROFILE_DRIVEN,
    WORKFLOW_ALLOWED_FOR_GENERATE_PRICING,
    WORKFLOW_STATUS_DIAGRAMS_GENERATED,
)
from app.models import Project
from app.repositories.project_repository import ProjectRepository
from app.services.catalog_service import CatalogService
from app.services.component_mapper_service import ComponentMapperService
from app.services.cost_estimator_service import CostEstimatorService

logger = logging.getLogger(__name__)

_PRICING_ELIGIBLE_STATUSES = WORKFLOW_ALLOWED_FOR_GENERATE_PRICING | {
    WORKFLOW_STATUS_DIAGRAMS_GENERATED,
}


class CostEstimateRefreshService:
    def __init__(
        self,
        db: Session,
        *,
        catalog_service: CatalogService | None = None,
        project_repo: ProjectRepository | None = None,
        cost_estimator: CostEstimatorService | None = None,
        mapper: ComponentMapperService | None = None,
    ) -> None:
        catalog = catalog_service or CatalogService(db)
        self._project_repo = project_repo or ProjectRepository(db)
        self._cost_estimator = cost_estimator or CostEstimatorService()
        self._mapper = mapper or ComponentMapperService(catalog)

    def ensure_current_estimates(self, project: Project) -> Project:
        if not self._can_refresh(project):
            return project
        self._ensure_architecture_approved(project)
        if not self._needs_refresh(project):
            return project
        logger.info("COST_ESTIMATE_STALE_RECALCULATING project_id=%s", project.id)
        return self._recalculate_and_persist(project)

    def recalculate_estimates(self, project: Project) -> Project:
        if not project.components:
            return project
        self._ensure_architecture_approved(project)
        return self._recalculate_and_persist(project)

    @staticmethod
    def _can_refresh(project: Project) -> bool:
        return bool(project.components) and project.workflow_status in _PRICING_ELIGIBLE_STATUSES

    @staticmethod
    def _needs_refresh(project: Project) -> bool:
        if not project.cost_estimates:
            return True
        return any(
            (estimate.calculator_version or "") != CALCULATOR_VERSION_PROFILE_DRIVEN
            for estimate in project.cost_estimates
        )

    def _ensure_architecture_approved(self, project: Project) -> None:
        if project.workflow_status != WORKFLOW_STATUS_DIAGRAMS_GENERATED:
            return
        self._project_repo.approve_architecture(project)

    def _recalculate_and_persist(self, project: Project) -> Project:
        mapped_components = self._mapper.map_components_from_db(project.components)
        costs = self._cost_estimator.estimate_from_components(
            components=mapped_components,
            expected_users=project.expected_users,
            stage=project.stage,
            capabilities=_project_capabilities(project),
            usage_profile=_project_usage_profile(project),
        )
        self._project_repo.persist_pricing(project, costs)
        self._project_repo.commit()
        self._project_repo.refresh(project)
        logger.info("COST_ESTIMATE_RECALCULATED_SUCCESSFULLY project_id=%s", project.id)
        return project


def _project_usage_profile(project: Project) -> dict[str, object] | None:
    answers = project.answers
    if answers is None or not answers.usage_profile:
        return None
    return dict(answers.usage_profile)


def _project_capabilities(project: Project) -> dict[str, bool]:
    answers = project.answers
    if answers is None:
        return {}
    return {
        "auth": bool(answers.auth),
        "file_upload": bool(answers.file_upload),
        "background_processing": bool(answers.background_processing),
        "dashboards": bool(answers.dashboards),
        "ai": bool(answers.ai),
        "payments": bool(answers.payments),
    }
