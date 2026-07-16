from app.services.component_selection_prompt_builder import ComponentSelectionPromptBuilder

CATEGORIES = [
    {"id": "compute", "name": "Compute", "description": "Runs application code."},
    {"id": "api", "name": "API Gateway", "description": "API entry point."},
]


def test_formats_requirements_as_human_readable_labels_not_raw_ids():
    prompt = ComponentSelectionPromptBuilder().build(
        application_description="A SaaS app",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={
            "background_processing": {"enabled": True},
            "payments": {"enabled": False},
            "dashboards_reports": {
                "enabled": True,
                "features": ["dashboard", "reports"],
            },
            "notifications": {
                "enabled": True,
                "channels": ["email", "push"],
            },
        },
        categories=CATEGORIES,
    )

    assert "Background processing: required" in prompt
    assert "Payments: not required" in prompt
    assert "Dashboards and reports: required" in prompt
    assert "Notifications: required" in prompt
    assert "channels: email, push" in prompt
    assert "Platform: Web" in prompt
    assert '"background_processing"' not in prompt
    assert '"payments"' not in prompt


def test_includes_valid_category_ids_list():
    prompt = ComponentSelectionPromptBuilder().build(
        application_description="A SaaS app",
        platform="mobile",
        stage="mvp",
        expected_users=1000,
        requirements={},
        categories=CATEGORIES,
    )

    assert "compute, api" in prompt
    assert "Platform: Mobile" in prompt
    assert "business requirement names" in prompt.lower()
