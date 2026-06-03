"""Tests for prompt construction."""

from __future__ import annotations

from app import models
from app.services.prompt_builder import build_generation_prompt


def test_includes_product_fields(sample_project):
    prompt = build_generation_prompt(sample_project)
    assert "TaskFlow" in prompt
    assert "team task management" in prompt
    assert "Web App" in prompt
    assert "MVP" in prompt
    assert "Up to 1,000" in prompt


def test_includes_all_requirement_answers(sample_project):
    prompt = build_generation_prompt(sample_project)
    assert "Authentication: Yes" in prompt
    assert "File uploads: Yes" in prompt
    assert "Background processing: No" in prompt
    assert "Edge cases" in prompt


def test_includes_json_schema_instructions():
    project = models.Project(
        name="Minimal",
        description="",
        project_types=["mobile_app"],
        stage="production",
        expected_users="100",
    )
    prompt = build_generation_prompt(project)
    assert '"cloud_options"' in prompt
    assert '"diagrams"' in prompt
    assert "Respond with JSON only" in prompt
    assert "Mobile App" in prompt
    assert "Production" in prompt


def test_handles_missing_answers():
    project = models.Project(
        name="Solo",
        description="Solo app",
        project_types=["web_app"],
        stage="mvp",
        expected_users="100",
    )
    prompt = build_generation_prompt(project)
    assert "Authentication: No" in prompt
