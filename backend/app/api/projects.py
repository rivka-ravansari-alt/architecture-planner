from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth.deps import get_current_user
from ..database import get_db
from ..project_types import PROJECT_TYPES
from ..services.generation import ArchitectureGenerationError, generate_for_project

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/project-types", response_model=list[schemas.ProjectTypeInfo])
def list_project_types() -> list[schemas.ProjectTypeInfo]:
    return [
        schemas.ProjectTypeInfo(id=item["type"], label=item["label"], description=item["description"])
        for item in PROJECT_TYPES
    ]


@router.post("/projects", response_model=schemas.ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.Project:
    project = models.Project(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        project_types=[t.value for t in payload.project_types],
        stage=payload.stage.value,
        expected_users=payload.expected_users.value,
    )
    project.answers = models.RequirementAnswers(**payload.answers.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _get_or_404(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/projects/{project_id}/generate", response_model=schemas.ProjectDetail)
def generate_project(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.Project:
    project = _get_or_404(db, project_id)
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    logger.info(
        "generate endpoint step=started status=started project_id=%s user_id=%s",
        project_id,
        user.id,
    )
    try:
        result = generate_for_project(db, project)
        logger.info(
            "generate endpoint step=complete status=completed project_id=%s",
            project_id,
        )
        return result
    except ArchitectureGenerationError as exc:
        logger.error(
            "generate endpoint step=failed status=failed project_id=%s reason=%s",
            project_id,
            exc.message,
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
