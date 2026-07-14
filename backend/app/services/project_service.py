"""Project business logic (Step 1 intake).

Persists the intake form only. No architecture generation, LLM calls, diagrams,
or pricing are triggered here.
"""

from __future__ import annotations

from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import UserOut
from app.schemas.project import CreateProjectRequest, CreateProjectResponse


class ProjectService:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._projects = project_repository

    def create(self, payload: CreateProjectRequest, user: UserOut) -> CreateProjectResponse:
        project_id = self._projects.create(payload, user.id)
        return CreateProjectResponse(id=project_id)
