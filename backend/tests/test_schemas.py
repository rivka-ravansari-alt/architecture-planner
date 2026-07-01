import pytest
from pydantic import ValidationError

from app.config.params import DESCRIPTION_MAX_CHARS
from app.schemas.project import ProjectCreate
from app.utils.token_estimate import estimate_token_count


def test_estimate_token_count_empty():
    assert estimate_token_count("") == 0


def test_estimate_token_count_short():
    assert estimate_token_count("hi") == 1


def test_rejects_description_over_char_limit():
    long_text = "x" * (DESCRIPTION_MAX_CHARS + 1)
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


def test_accepts_custom_expected_users_and_usage_profile():
    project = ProjectCreate(
        name="Test",
        description="Valid description.",
        project_types=["web_app"],
        expected_users="2500",
        usage_profile={
            "monthly_active_users": "custom",
            "custom_monthly_active_users": 2500,
            "user_activity": "heavy",
            "background_jobs": "moderate",
        },
    )
    assert project.expected_users == "2500"
    assert project.usage_profile is not None
    assert project.usage_profile.user_activity == "heavy"


def test_accepts_small_custom_expected_users_count():
    project = ProjectCreate(
        name="Test",
        description="Valid description.",
        project_types=["web_app"],
        expected_users="150",
    )
    assert project.expected_users == "150"


def test_accepts_numeric_expected_users_count():
    project = ProjectCreate(
        name="Test",
        description="Valid description.",
        project_types=["web_app"],
        expected_users=150,
    )
    assert project.expected_users == "150"
