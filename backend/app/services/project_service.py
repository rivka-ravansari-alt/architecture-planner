"""Project business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.params import ERR_PROJECT_FORBIDDEN, ERR_PROJECT_NOT_FOUND
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Project, User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, db: Session, repository: ProjectRepository | None = None) -> None:
        self._repo = repository or ProjectRepository(db)

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
