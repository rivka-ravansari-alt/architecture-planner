"""Project persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config.params import (
    CALCULATOR_VERSION_PROFILE_DRIVEN,
    COMPONENT_CATEGORY_CORE,
    COMPONENT_CATEGORY_OPTIONAL,
    COMPONENT_SOURCE_AI,
    WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
    WORKFLOW_STATUS_COMPONENTS_APPROVED,
    WORKFLOW_STATUS_COMPONENTS_GENERATED,
    WORKFLOW_STATUS_DIAGRAMS_GENERATED,
    WORKFLOW_STATUS_DRAFT,
    WORKFLOW_STATUS_PRICING_GENERATED,
)
from app.models import (
    CloudMapping,
    CostEstimate,
    Project,
    ProjectComponent,
    RequirementAnswers,
)
from app.repositories.base import BaseRepository
from app.schemas.domain import MappedComponent, ProviderCost
from app.schemas.project import ComponentUpdateIn, ProjectCreate


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
            expected_users=payload.expected_users,
            workflow_status=WORKFLOW_STATUS_DRAFT,
        )
        project.answers = RequirementAnswers(
            **payload.answers.model_dump(),
            usage_profile=(
                payload.usage_profile.model_dump() if payload.usage_profile is not None else None
            ),
        )
        self._db.add(project)
        return project

    def clear_components(self, project: Project) -> None:
        project.components.clear()

    def clear_diagrams(self, project: Project) -> None:
        project.main_flow = []
        project.architecture_summary = ""
        project.architecture_diagrams = None
        project.architecture_diagram = None

    def clear_pricing(self, project: Project) -> None:
        project.cost_estimates.clear()

    def clear_generated_content(self, project: Project) -> None:
        self.clear_components(project)
        self.clear_pricing(project)
        project.risks.clear()
        project.recommendations.clear()
        self.clear_diagrams(project)

    def persist_components(self, project: Project, components: list[MappedComponent]) -> None:
        self.clear_components(project)
        self.clear_diagrams(project)
        self.clear_pricing(project)
        self._add_components(project, components)
        project.workflow_status = WORKFLOW_STATUS_COMPONENTS_GENERATED

    def replace_components(self, project: Project, payload: list[ComponentUpdateIn]) -> None:
        self.clear_components(project)
        for order, item in enumerate(payload):
            category = COMPONENT_CATEGORY_OPTIONAL if item.optional else COMPONENT_CATEGORY_CORE
            component = ProjectComponent(
                key=item.key,
                name=item.name,
                component_type=item.type,
                reason=item.reason,
                category=category,
                source=item.source or COMPONENT_SOURCE_AI,
                optional=item.optional,
                order=order * 10,
                implementation_options=item.implementation_options,
            )
            cloud = item.cloud_mapping
            component.cloud_mapping = CloudMapping(
                aws=cloud.aws if cloud else [],
                gcp=cloud.gcp if cloud else [],
                azure=cloud.azure if cloud else [],
            )
            project.components.append(component)
        project.workflow_status = WORKFLOW_STATUS_COMPONENTS_APPROVED

    def persist_diagrams(
        self,
        project: Project,
        *,
        main_flow: list[str],
        architecture_summary: str,
        architecture_diagrams: dict,
    ) -> None:
        self.clear_diagrams(project)
        self.clear_pricing(project)
        project.main_flow = main_flow
        project.next_steps = []
        project.architecture_summary = architecture_summary
        project.architecture_diagrams = architecture_diagrams
        project.architecture_diagram = None
        project.workflow_status = WORKFLOW_STATUS_DIAGRAMS_GENERATED

    def approve_architecture(self, project: Project) -> None:
        project.workflow_status = WORKFLOW_STATUS_ARCHITECTURE_APPROVED

    def persist_pricing(self, project: Project, costs: list[ProviderCost]) -> None:
        self.clear_pricing(project)
        self._add_costs(project, costs)
        project.workflow_status = WORKFLOW_STATUS_PRICING_GENERATED
        project.generated_at = datetime.now(timezone.utc)

    def persist_architecture(
        self,
        project: Project,
        *,
        components: list[MappedComponent],
        costs: list[ProviderCost],
        main_flow: list[str],
        architecture_summary: str,
        architecture_diagrams: dict,
    ) -> None:
        self.clear_generated_content(project)
        self._add_components(project, components)
        self._add_costs(project, costs)
        project.main_flow = main_flow
        project.next_steps = []
        project.architecture_summary = architecture_summary
        project.architecture_diagrams = architecture_diagrams
        project.architecture_diagram = None
        project.generated_at = datetime.now(timezone.utc)
        project.workflow_status = WORKFLOW_STATUS_PRICING_GENERATED

    def _add_components(self, project: Project, components: list[MappedComponent]) -> None:
        for comp in components:
            component = ProjectComponent(
                key=comp.key,
                name=comp.name,
                component_type=comp.component_type,
                reason=comp.reason,
                category=comp.category,
                source=comp.source or COMPONENT_SOURCE_AI,
                optional=comp.optional,
                order=comp.order,
                implementation_options=comp.implementation_options or None,
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
                    monthly_low=cost.required_low,
                    monthly_high=cost.required_high,
                    required_monthly_low=cost.required_low,
                    required_monthly_high=cost.required_high,
                    optional_monthly_low=cost.optional_low,
                    optional_monthly_high=cost.optional_high,
                    currency=cost.currency,
                    notes=cost.notes,
                    unknown_items=list(cost.unknown_items),
                    warnings=list(cost.warnings),
                    component_breakdown=list(cost.component_breakdown),
                    pricing_debug_table=list(cost.pricing_debug_table or cost.component_breakdown),
                    calculator_version=cost.calculator_version or CALCULATOR_VERSION_PROFILE_DRIVEN,
                )
            )
