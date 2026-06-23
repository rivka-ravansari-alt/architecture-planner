"""Project route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.controllers.project_controller import ProjectController
from app.core.dependencies import (
    get_catalog_service,
    get_current_user,
    get_generation_service,
    get_project_service,
)
from app.models import User
from app.schemas.project import ComponentsUpdate, ProjectCreate, ProjectDetail, ProjectTypeInfo
from app.services.catalog_service import CatalogService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService


def _controller(
    project_service: ProjectService = Depends(get_project_service),
    generation_service: GenerationService = Depends(get_generation_service),
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> ProjectController:
    return ProjectController(project_service, generation_service, catalog_service)


router = APIRouter(tags=["projects"])


@router.get("/project-types", response_model=list[ProjectTypeInfo])
def list_project_types(controller: ProjectController = Depends(_controller)):
    return controller.list_project_types()


@router.post("/projects", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.create_project(payload, user)


@router.post("/projects/{project_id}/generate", response_model=ProjectDetail)
def generate_project(
    project_id: str,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.generate_project(project_id, user)


@router.post("/projects/{project_id}/generate-components", response_model=ProjectDetail)
def generate_components(
    project_id: str,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.generate_components(project_id, user)


@router.put("/projects/{project_id}/components", response_model=ProjectDetail)
def update_components(
    project_id: str,
    payload: ComponentsUpdate,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.update_components(project_id, payload, user)


@router.post("/projects/{project_id}/generate-diagrams", response_model=ProjectDetail)
def generate_diagrams(
    project_id: str,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.generate_diagrams(project_id, user)


@router.post("/projects/{project_id}/approve-architecture", response_model=ProjectDetail)
def approve_architecture(
    project_id: str,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.approve_architecture(project_id, user)


@router.post("/projects/{project_id}/generate-pricing", response_model=ProjectDetail)
def generate_pricing(
    project_id: str,
    user: User = Depends(get_current_user),
    controller: ProjectController = Depends(_controller),
):
    return controller.generate_pricing(project_id, user)
