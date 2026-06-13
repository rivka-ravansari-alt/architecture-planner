"""Tests for AI generation orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.clients.ai_client import BaseAIClient
from app.config.params import (
    GENERATION_REQUEST_FILENAME,
    GENERATION_RESPONSE_FILENAME,
    GENERATION_STORAGE_PREFIX,
)
from app.core.exceptions import AIClientError, ArchitectureGenerationError
from app.models import ArchitectureGenerationRequest
from app.services.generation_service import GenerationService
from tests.conftest import MockAIClient


def test_success_persists_ai_output(db_session, sample_project, mock_ai_client, ai_dirs):
    storage_dir = ai_dirs
    result = GenerationService(db_session, ai_client=mock_ai_client).generate(sample_project)

    assert result.generated_at is not None
    assert len(result.components) == 4
    assert result.architecture_summary.startswith("A browser client")
    assert result.cost_breakdown is not None
    assert set(result.cost_breakdown["cloud_cost"]) == {"aws", "gcp", "azure"}
    assert result.cost_breakdown["total_monthly_cost"]["low"] >= 0
    assert result.architecture_diagrams is not None
    assert "high_level" in result.architecture_diagrams
    assert "system_flow" in result.architecture_diagrams
    assert "technical_architecture" in result.architecture_diagrams
    assert "technical_flow" not in result.architecture_diagrams

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

    gen_dir = storage_dir / GENERATION_STORAGE_PREFIX / request.id
    request_json = json.loads(
        (gen_dir / GENERATION_REQUEST_FILENAME).read_text(encoding="utf-8")
    )
    response_json = json.loads(
        (gen_dir / GENERATION_RESPONSE_FILENAME).read_text(encoding="utf-8")
    )
    assert request_json["project_id"] == sample_project.id
    assert request_json["user_id"] == sample_project.user_id
    assert request_json["generated_prompt"]
    assert "TaskFlow" in request_json["generated_prompt"]
    assert response_json["validation_result"] == {"valid": True}
    assert response_json["parsed_response"] is not None
    assert response_json["parsed_response"]["architecture"]["summary"] == (
        result.architecture_summary
    )
    assert response_json["duration_seconds"] is not None


def test_invalid_ai_response_marks_request_failed(db_session, sample_project, ai_dirs):
    storage_dir = ai_dirs
    service = GenerationService(db_session, ai_client=MockAIClient('{"not": "valid architecture"}'))

    with pytest.raises(ArchitectureGenerationError):
        service.generate(sample_project)

    request = db_session.scalar(select(ArchitectureGenerationRequest))
    assert request.status == "failed"
    assert sample_project.components == []

    response_json = json.loads(
        (
            storage_dir
            / GENERATION_STORAGE_PREFIX
            / request.id
            / GENERATION_RESPONSE_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert response_json["errors"]
    assert response_json["raw_ai_response"] is not None


def test_ai_client_error_raises_and_marks_failed(db_session, sample_project, ai_dirs):
    storage_dir = ai_dirs

    class FailingClient(BaseAIClient):
        def generate(self, prompt: str) -> str:
            raise AIClientError("network down")

    service = GenerationService(db_session, ai_client=FailingClient())

    with pytest.raises(ArchitectureGenerationError, match="network down"):
        service.generate(sample_project)

    request = db_session.scalar(select(ArchitectureGenerationRequest))
    assert request.status == "failed"

    response_json = json.loads(
        (
            storage_dir
            / GENERATION_STORAGE_PREFIX
            / request.id
            / GENERATION_RESPONSE_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert response_json["errors"] == ["network down"]
    assert response_json["duration_seconds"] is not None


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
