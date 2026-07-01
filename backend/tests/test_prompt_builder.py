def test_includes_project_name(sample_project, prompt_builder):
    components_prompt = prompt_builder.build_components(sample_project)
    assert "Expected monthly active users: 1,000" in components_prompt
    assert "File uploads: Yes" in components_prompt
    assert "TaskFlow" in components_prompt
    assert '"components"' in components_prompt
    assert "diagrams" not in components_prompt.lower()
    assert "Application platform: Web Application" in components_prompt
    assert "Platform considerations" in components_prompt
    assert "complete runnable architecture" in components_prompt
    assert "## Usage profile" in components_prompt


def test_components_prompt_includes_mobile_platform(db_session, test_user, prompt_builder):
    from app.models import Project

    project = Project(
        user_id=test_user.id,
        name="MobileApp",
        description="A mobile-only product.",
        project_types=["mobile_app"],
        stage="mvp",
        expected_users="100",
    )
    db_session.add(project)
    db_session.commit()
    prompt = prompt_builder.build_components(project)
    assert "Application platform: Mobile Application" in prompt
    assert "The application platform must influence component selection" in prompt
    assert "mobile_app" in prompt


def test_components_prompt_includes_both_platforms(db_session, test_user, prompt_builder):
    from app.models import Project

    project = Project(
        user_id=test_user.id,
        name="CrossPlatform",
        description="Web and mobile product.",
        project_types=["web_app", "mobile_app"],
        stage="mvp",
        expected_users="1000",
    )
    db_session.add(project)
    db_session.commit()
    prompt = prompt_builder.build_components(project)
    assert "Application platform: Both Web and Mobile" in prompt
    assert "Platform-specific requirements and capabilities" in prompt


def test_components_prompt_includes_catalog_descriptions(sample_project, prompt_builder):
    prompt = prompt_builder.build_components(sample_project)
    assert "service:\n" in prompt
    assert "Backend execution component that implements business logic" in prompt
    assert "api_gateway:\n" in prompt
    assert "Routes traffic to backend services" in prompt


def test_handles_missing_answers(db_session, test_user, prompt_builder):
    from app.models import Project

    project = Project(
        user_id=test_user.id,
        name="Bare",
        description="Minimal project.",
        project_types=["web_app"],
        stage="mvp",
        expected_users="100",
    )
    db_session.add(project)
    db_session.commit()
    prompt = prompt_builder.build_components(project)
    assert "Authentication: No" in prompt


def test_components_prompt_uses_usage_profile_when_present(db_session, test_user, prompt_builder):
    from app.models import Project, RequirementAnswers

    project = Project(
        user_id=test_user.id,
        name="AI Platform",
        description="An AI-heavy product.",
        project_types=["web_app"],
        stage="mvp",
        expected_users="10000",
    )
    project.answers = RequirementAnswers(
        auth=True,
        ai=True,
        usage_profile={
            "monthly_active_users": "10000",
            "user_activity": "heavy",
            "background_jobs": "moderate",
            "file_uploads_enabled": False,
            "ai_enabled": True,
            "ai_requests_per_user_per_day": "5_20",
            "prompt_size": "large",
            "response_size": "medium",
            "notification_channels": ["email", "push"],
            "notifications_per_month": "10k_100k",
        },
    )
    db_session.add(project)
    db_session.commit()

    prompt = prompt_builder.build_components(project)

    assert "Expected monthly active users: 10,000" in prompt
    assert "Average user activity: Heavy (20–100 actions per day)" in prompt
    assert "Background tasks: Moderate" in prompt
    assert "Artificial intelligence: Yes" in prompt
    assert "Notifications: Yes" in prompt
    assert "queues/workers for background tasks" in prompt
    assert "Authentication: Yes" not in prompt
