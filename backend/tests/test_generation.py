"""Tests for AI generation orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.clients.ai_client import BaseAIClient
from app.core.exceptions import AIClientError, ArchitectureGenerationError
from app.models import ArchitectureGenerationRequest
from app.services.generation_service import GenerationService, generate_for_project
from tests.conftest import MockAIClient
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_success_persists_ai_output(db_session, sample_project, mock_ai_client, ai_dirs):
    prompts_dir, outputs_dir = ai_dirs
    result = GenerationService(db_session, ai_client=mock_ai_client).generate(sample_project)

    assert result.generated_at is not None
    assert len(result.components) == 4
    assert result.architecture_summary.startswith("A browser client")
    assert len(result.risks) == 1
    assert len(result.recommendations) == 2
    assert result.next_steps[0].startswith("Confirm")
    assert len(result.cost_estimates) == 3
    assert result.architecture_diagrams is not None
    assert "high_level" in result.architecture_diagrams
    assert "system_flow" in result.architecture_diagrams
    assert "technical_flow" in result.architecture_diagrams

    request = db_session.scalar(
        select(ArchitectureGenerationRequest).where(
            ArchitectureGenerationRequest.project_id == sample_project.id
        )
    )
    assert request is not None
    assert request.status == "completed"
    assert request.input_os_path
    assert request.output_os_path
    assert Path(request.input_os_path).exists()
    assert Path(request.output_os_path).exists()
    saved = json.loads(Path(request.output_os_path).read_text(encoding="utf-8"))
    assert saved["architecture"]["summary"] == result.architecture_summary
    assert "TaskFlow" in Path(request.input_os_path).read_text(encoding="utf-8")


def test_invalid_ai_response_marks_request_failed(db_session, sample_project, ai_dirs):
    service = GenerationService(db_session, ai_client=MockAIClient('{"not": "valid architecture"}'))

    with pytest.raises(ArchitectureGenerationError):
        service.generate(sample_project)

    request = db_session.scalar(select(ArchitectureGenerationRequest))
    assert request.status == "failed"
    assert sample_project.components == []


def test_ai_client_error_raises_and_marks_failed(db_session, sample_project, ai_dirs):
    class FailingClient(BaseAIClient):
        def generate(self, prompt: str) -> str:
            raise AIClientError("network down")

    service = GenerationService(db_session, ai_client=FailingClient())

    with pytest.raises(ArchitectureGenerationError, match="network down"):
        service.generate(sample_project)

    request = db_session.scalar(select(ArchitectureGenerationRequest))
    assert request.status == "failed"


def test_regeneration_replaces_previous_output(
    db_session, sample_project, mock_ai_client, ai_dirs
):
    service = GenerationService(db_session, ai_client=mock_ai_client)
    service.generate(sample_project)
    first_count = len(sample_project.components)

    service.generate(sample_project)
    assert len(sample_project.components) == first_count

    requests = db_session.scalars(select(ArchitectureGenerationRequest)).all()
    assert len(requests) == 2
    assert requests[-1].status == "completed"
