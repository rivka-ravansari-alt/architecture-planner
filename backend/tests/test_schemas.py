import pytest
from pydantic import ValidationError

from app.config.params import DESCRIPTION_MAX_TOKENS
from app.schemas.project import ProjectCreate
from app.utils.token_estimate import estimate_token_count


def test_estimate_token_count_empty():
    assert estimate_token_count("") == 0


def test_estimate_token_count_short():
    assert estimate_token_count("hi") == 1


def test_rejects_description_over_token_limit():
    long_text = "word " * (DESCRIPTION_MAX_TOKENS + 10)
    with pytest.raises(ValidationError):
        ProjectCreate(
            name="Test",
            description=long_text,
            project_types=["web_app"],
        )


def test_dedupes_project_types():
    project = ProjectCreate(
        name="Test",
        description="Valid description.",
        project_types=["web_app", "web_app", "mobile_app"],
    )
    assert project.project_types == ["web_app", "mobile_app"]
