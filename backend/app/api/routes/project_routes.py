"""Project route definitions (Step 1 intake + Step 2 component selection).

The router never touches Firestore or OpenAI directly: it delegates to the
controller -> service(s) -> repository / clients.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.controllers.project_controller import ProjectController
from app.core.dependencies import get_current_user, get_project_controller
from app.schemas.auth import UserOut
from app.schemas.component_selection import (
    AddComponentRequest,
    ArchitectureCategoryOut,
    ComponentSelectionResponse,
)
from app.schemas.global_usage_model import GlobalUsageModelResponse
from app.schemas.pricing import PricingRunResponse, ProviderPricingResponse
from app.schemas.project import CreateProjectRequest, CreateProjectResponse

router = APIRouter(tags=["projects"])


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> CreateProjectResponse:
    return controller.create_project(payload, user)


@router.post("/projects/{project_id}/architecture-components/generate")
def generate_architecture_components(
    project_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> ComponentSelectionResponse:
    return controller.generate_architecture_components(project_id, user)


@router.get("/projects/{project_id}/architecture-components/selection")
def get_architecture_selection(
    project_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> ComponentSelectionResponse:
    return controller.get_architecture_selection(project_id, user)


@router.get("/architecture-categories")
def list_architecture_categories(
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> list[ArchitectureCategoryOut]:
    return controller.list_architecture_categories(user)


@router.post("/projects/{project_id}/architecture-components")
def add_architecture_component(
    project_id: str,
    payload: AddComponentRequest,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> ComponentSelectionResponse:
    return controller.add_architecture_component(project_id, payload, user)


@router.delete("/projects/{project_id}/architecture-components/{instance_id}")
def remove_architecture_component(
    project_id: str,
    instance_id: str,
    selection_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> ComponentSelectionResponse:
    return controller.remove_architecture_component(
        project_id, selection_id, instance_id, user
    )


@router.post("/projects/{project_id}/usage-model/generate")
def generate_global_usage_model(
    project_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> GlobalUsageModelResponse:
    return controller.generate_global_usage_model(project_id, user)


@router.get("/projects/{project_id}/usage-model")
def get_global_usage_model(
    project_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> GlobalUsageModelResponse:
    return controller.get_global_usage_model(project_id, user)


@router.post("/projects/{project_id}/pricing/generate/{provider}")
def generate_provider_pricing(
    project_id: str,
    provider: str,
    run_id: str | None = None,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> ProviderPricingResponse:
    return controller.generate_provider_pricing(
        project_id, provider, user, run_id=run_id
    )


@router.get("/projects/{project_id}/pricing")
def get_latest_pricing(
    project_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> PricingRunResponse:
    return controller.get_latest_pricing(project_id, user)


@router.get("/projects/{project_id}/pricing/runs/{run_id}")
def get_pricing_run(
    project_id: str,
    run_id: str,
    user: UserOut = Depends(get_current_user),
    controller: ProjectController = Depends(get_project_controller),
) -> PricingRunResponse:
    return controller.get_pricing_run(project_id, run_id, user)
