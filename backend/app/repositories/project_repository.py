"""Project persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    ArchitectureComponent,
    CloudMapping,
    CostEstimate,
    Project,
    Recommendation,
    RequirementAnswers,
    Risk,
)
from app.repositories.base import BaseRepository
from app.schemas.domain import MappedComponent, MappedRisk, ProviderCost
from app.schemas.project import ProjectCreate


class ProjectRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def find_by_id(self, project_id: str) -> Project | None:
        return self._db.get(Project, project_id)

    def create(self, payload: ProjectCreate, user_id: str) -> Project:
        project = Project(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            project_types=[project_type.value for project_type in payload.project_types],
            stage=payload.stage.value,
            expected_users=payload.expected_users.value,
        )
        project.answers = RequirementAnswers(**payload.answers.model_dump())
        self._db.add(project)
        return project

    def clear_generated_content(self, project: Project) -> None:
        project.components.clear()
        project.cost_estimates.clear()
        project.risks.clear()
        project.recommendations.clear()

    def persist_architecture(
        self,
        project: Project,
        *,
        components: list[MappedComponent],
        costs: list[ProviderCost],
        risks: list[MappedRisk],
        recommendations: list[str],
        main_flow: list[str],
        next_steps: list[str],
        architecture_summary: str,
        architecture_diagrams: dict,
    ) -> None:
        self.clear_generated_content(project)
        self._add_components(project, components)
        self._add_costs(project, costs)
        self._add_risks(project, risks)
        self._add_recommendations(project, recommendations)
        project.main_flow = main_flow
        project.next_steps = next_steps
        project.architecture_summary = architecture_summary
        project.architecture_diagrams = architecture_diagrams
        project.architecture_diagram = None
        project.generated_at = datetime.now(timezone.utc)

    def _add_components(self, project: Project, components: list[MappedComponent]) -> None:
        for comp in components:
            component = ArchitectureComponent(
                key=comp.key,
                name=comp.name,
                component_type=comp.component_type,
                reason=comp.reason,
                category=comp.category,
                optional=comp.optional,
                order=comp.order,
            )
            component.cloud_mapping = CloudMapping(
                aws=comp.cloud.get("aws", []),
                gcp=comp.cloud.get("gcp", []),
                azure=comp.cloud.get("azure", []),
            )
            project.components.append(component)

    def _add_costs(self, project: Project, costs: list[ProviderCost]) -> None:
        for cost in costs:
            project.cost_estimates.append(
                CostEstimate(
                    provider=cost.provider,
                    monthly_low=cost.monthly_low,
                    monthly_high=cost.monthly_high,
                    currency=cost.currency,
                    notes=cost.notes,
                )
            )

    def _add_risks(self, project: Project, risks: list[MappedRisk]) -> None:
        for risk in risks:
            project.risks.append(
                Risk(title=risk.title, description=risk.description, severity=risk.severity)
            )

    def _add_recommendations(self, project: Project, recommendations: list[str]) -> None:
        for recommendation in recommendations:
            project.recommendations.append(Recommendation(text=recommendation))
