from app.models import Project, RequirementAnswers
from app.services.prompt_builder_service import PromptBuilderService


def test_includes_project_name(sample_project):
    builder = PromptBuilderService()
    prompt = builder.build(sample_project)
    assert "TaskFlow" in prompt
    assert "Authentication: Yes" in prompt
    assert "File uploads: Yes" in prompt

    components_prompt = builder.build_components(sample_project)
    assert "TaskFlow" in components_prompt
    assert '"components"' in components_prompt
    assert "diagrams" not in components_prompt.lower() or "do not include" in components_prompt.lower()


def test_handles_missing_answers(db_session, test_user):
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
    prompt = PromptBuilderService().build(project)
    assert "Authentication: No" in prompt
