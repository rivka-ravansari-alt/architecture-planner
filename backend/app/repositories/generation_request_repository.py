"""Architecture generation request persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config.params import GENERATION_STATUS_COMPLETED, GENERATION_STATUS_FAILED, GENERATION_STATUS_PENDING
from app.models import ArchitectureGenerationRequest, Project
from app.repositories.base import BaseRepository


class GenerationRequestRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_pending(self, project: Project) -> ArchitectureGenerationRequest:
        now = datetime.now(timezone.utc)
        request = ArchitectureGenerationRequest(
            status=GENERATION_STATUS_PENDING,
            project_id=project.id,
            start_time=now,
        )
        self._db.add(request)
        return request

    def save_prompt_path(self, request: ArchitectureGenerationRequest, path: str) -> None:
        request.input_os_path = path
        request.updated_at = datetime.now(timezone.utc)

    def save_output_path(self, request: ArchitectureGenerationRequest, path: str) -> None:
        request.output_os_path = path
        request.updated_at = datetime.now(timezone.utc)

    def mark_completed(self, request: ArchitectureGenerationRequest) -> None:
        now = datetime.now(timezone.utc)
        request.status = GENERATION_STATUS_COMPLETED
        request.end_time = now
        request.updated_at = now

    def mark_failed(self, request: ArchitectureGenerationRequest) -> None:
        now = datetime.now(timezone.utc)
        request.status = GENERATION_STATUS_FAILED
        request.end_time = now
        request.updated_at = now
