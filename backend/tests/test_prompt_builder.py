def test_includes_project_name(sample_project, prompt_builder):
    components_prompt = prompt_builder.build_components(sample_project)
    assert "Authentication: Yes" in components_prompt
    assert "File uploads: Yes" in components_prompt
    assert "TaskFlow" in components_prompt
    assert '"components"' in components_prompt
    assert "diagrams" not in components_prompt.lower()
    assert "Application platform: Web Application" in components_prompt
    assert "Platform considerations" in components_prompt
    assert "complete runnable architecture" in components_prompt


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
