"""Tests for request/response schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import DESCRIPTION_MAX_TOKENS, ProjectCreate, estimate_token_count


def test_estimate_token_count_empty():
    assert estimate_token_count("") == 0
    assert estimate_token_count("   ") == 0


def test_estimate_token_count_non_empty():
    assert estimate_token_count("hello") == 2
    assert estimate_token_count("a" * 400) == 100


def test_project_create_rejects_description_over_token_limit():
    over_limit = "a" * (DESCRIPTION_MAX_TOKENS * 4 + 1)
    with pytest.raises(ValidationError):
        ProjectCreate(
            name="Test App",
            description=over_limit,
            project_types=["web_app"],
        )


def test_project_create_accepts_description_at_token_limit():
    at_limit = "a" * (DESCRIPTION_MAX_TOKENS * 4)
    project = ProjectCreate(
        name="Test App",
        description=at_limit,
        project_types=["web_app"],
    )
    assert project.description == at_limit
