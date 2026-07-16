"""Project HTTP controller (Step 1 intake + Step 2 component selection)."""

from __future__ import annotations

from app.schemas.auth import UserOut
from app.schemas.component_selection import (
    AddComponentRequest,
    ArchitectureCategoryOut,
    ComponentSelectionResponse,
)
from app.schemas.global_usage_model import GlobalUsageModelResponse
from app.schemas.pricing import PricingRunResponse, ProviderPricingResponse
from app.schemas.project import CreateProjectRequest, CreateProjectResponse
from app.services.architecture_component_service import ArchitectureComponentService
from app.services.global_usage_service import GlobalUsageService
from app.services.pricing_service import PricingService
from app.services.project_service import ProjectService


class ProjectController:
    def __init__(
        self,
        project_service: ProjectService,
        architecture_component_service: ArchitectureComponentService,
        global_usage_service: GlobalUsageService,
        pricing_service: PricingService,
    ) -> None:
        self._service = project_service
        self._architecture_components = architecture_component_service
        self._global_usage = global_usage_service
        self._pricing = pricing_service

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

    def generate_global_usage_model(
        self, project_id: str, user: UserOut
    ) -> GlobalUsageModelResponse:
        return self._global_usage.generate(project_id, user)

    def get_global_usage_model(
        self, project_id: str, user: UserOut
    ) -> GlobalUsageModelResponse:
        return self._global_usage.get_usage_model(project_id, user)

    def generate_provider_pricing(
        self,
        project_id: str,
        provider: str,
        user: UserOut,
        *,
        run_id: str | None = None,
    ) -> ProviderPricingResponse:
        return self._pricing.generate_provider(
            project_id, provider, user, run_id=run_id
        )

    def get_latest_pricing(
        self, project_id: str, user: UserOut
    ) -> PricingRunResponse:
        return self._pricing.get_latest_pricing(project_id, user)

    def get_pricing_run(
        self, project_id: str, run_id: str, user: UserOut
    ) -> PricingRunResponse:
        return self._pricing.get_pricing_run(project_id, run_id, user)
