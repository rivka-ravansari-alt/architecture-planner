"""Unit tests for the global usage model orchestrator (Step 3)."""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.schemas.auth import UserOut
from app.schemas.global_usage_model import GlobalUsageModelEstimateResult, GlobalUsageModelResult, UsageParameterEstimate
from app.services.global_usage_service import GlobalUsageService
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_parameter_resolver import ResolvedUsageParameters, UsageParameterResolver


class FakeProjectRepository:
    def __init__(self) -> None:
        self.saved_documents: list[dict] = []
        self.saved_by_id: dict[str, dict] = {}
        self.stale_models: set[str] = set()
        self.stale_runs: set[str] = set()

    def find_by_id(self, project_id: str):
        if project_id != "project-1":
            return None
        return {
            "id": project_id,
            "user_id": "user-1",
            "description": "A team task manager.",
            "platform": "mobile",
            "stage": "mvp",
            "expected_users": 1000,
            "requirements": {"authentication": {"enabled": True}},
        }

    def get_latest_architecture_selection(self, project_id: str):
        return {
            "id": "selection-1",
            "selected": [
                {
                    "category_id": "compute",
                    "name": "Compute",
                    "description": "Runs application code.",
                    "reason": "Needed for APIs.",
                }
            ],
        }

    def save_global_usage_model(self, project_id: str, usage_model: dict) -> str:
        self.saved_documents.append({"project_id": project_id, **usage_model})
        return "model-1"

    def get_global_usage_model(self, project_id: str, model_id: str):
        document = self.saved_by_id.get(model_id)
        if document is None:
            return None
        return {"id": model_id, **document}

    def create_global_usage_model_if_absent(
        self, project_id: str, model_id: str, usage_model: dict
    ):
        existing = self.saved_by_id.get(model_id)
        if existing is not None and not existing.get("stale"):
            return model_id, False
        self.saved_by_id[model_id] = usage_model
        self.saved_documents.append({"project_id": project_id, **usage_model})
        return model_id, True

    def get_latest_global_usage_model(self, project_id: str):
        if "model-1" in self.stale_models:
            return {
                "id": "model-1",
                "selection_id": "selection-1",
                "stale": True,
                "usage_model": {"llm": {}, "static": {}},
            }
        if not self.saved_documents:
            return None
        saved = self.saved_documents[-1]
        return {
            "id": "model-1",
            "selection_id": saved.get("selection_id", "selection-1"),
            "usage_model": saved.get("usage_model", {"llm": {}, "static": {}}),
            "llm_parameters": saved.get("llm_parameters", []),
            "static_parameters": saved.get("static_parameters", []),
        }

    def mark_global_usage_model_stale(self, project_id: str, model_id: str) -> None:
        self.stale_models.add(model_id)

    def mark_pricing_run_stale(self, project_id: str, run_id: str) -> None:
        self.stale_runs.add(run_id)

    def invalidate_downstream_artifacts(self, project_id: str) -> None:
        self.stale_models.add("model-1")
        self.stale_runs.add("run-1")


class FakeParameterResolver:
    def resolve_for_selected_components(self, selected_components):
        return ResolvedUsageParameters(
            llm=["requests_per_user_per_month"],
            static=["users", "stage"],
        )


class FakeUsageModelService:
    captured_prompt: str | None = None

    def estimate(self, **kwargs):
        assert kwargs["platform"] == "mobile"
        assert kwargs["usage_parameters"] == ["requests_per_user_per_month"]
        raw_response = (
            '{"usage": {"requests_per_user_per_month": '
            '{"value": 120, "reason": "Typical CRUD usage per active user."}}}'
        )
        return GlobalUsageModelEstimateResult(
            result=GlobalUsageModelResult(
                usage={
                    "requests_per_user_per_month": UsageParameterEstimate(
                        value=120,
                        reason="Typical CRUD usage per active user.",
                    ),
                }
            ),
            prompt="exact prompt sent to OpenAI",
            raw_response=raw_response,
        )


def test_generate_persists_and_returns_combined_usage_model():
    projects = FakeProjectRepository()
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    response = service.generate("project-1", user)

    assert isinstance(response.model_id, str) and response.model_id
    assert response.selection_id == "selection-1"
    assert response.llm_parameters == ["requests_per_user_per_month"]
    assert response.static_parameters == ["users", "stage"]
    assert response.llm["requests_per_user_per_month"].value == 120
    assert response.static == {"users": 1000, "stage": "mvp"}

    saved = projects.saved_documents[0]
    assert saved["usage_model"]["llm"]["requests_per_user_per_month"]["value"] == 120
    assert saved["usage_model"]["static"] == {"users": 1000, "stage": "mvp"}
    assert saved["prompt"] == "exact prompt sent to OpenAI"
    assert saved["raw_response"] == (
        '{"usage": {"requests_per_user_per_month": '
        '{"value": 120, "reason": "Typical CRUD usage per active user."}}}'
    )
    assert saved["model_output"]["usage"]["requests_per_user_per_month"]["value"] == 120
    assert saved["selection_id"] == "selection-1"
    assert saved["input"]["platform"] == "mobile"
    assert saved["created_at"] is not None


def test_generate_raises_when_no_parameters_can_be_resolved():
    projects = FakeProjectRepository()

    class EmptyParameterResolver:
        def resolve_for_selected_components(self, selected_components):
            return ResolvedUsageParameters(llm=[], static=[])

    service = GlobalUsageService(
        projects,
        EmptyParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    with pytest.raises(ServiceUnavailableError, match="No usage parameters"):
        service.generate("project-1", user)


def test_generate_raises_when_project_is_missing():
    projects = FakeProjectRepository()
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    with pytest.raises(NotFoundError):
        service.generate("missing-project", user)


def test_get_usage_model_raises_when_stale():
    projects = FakeProjectRepository()
    projects.stale_models.add("model-1")
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    with pytest.raises(NotFoundError, match="No global usage model exists"):
        service.get_usage_model("project-1", user)


def test_get_usage_model_raises_when_selection_id_mismatch():
    projects = FakeProjectRepository()
    projects.saved_documents.append(
        {
            "selection_id": "old-selection",
            "usage_model": {"llm": {}, "static": {"users": 1000}},
            "llm_parameters": [],
            "static_parameters": ["users"],
        }
    )
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    with pytest.raises(NotFoundError, match="No global usage model exists"):
        service.get_usage_model("project-1", user)


def test_generate_is_idempotent_for_identical_inputs():
    projects = FakeProjectRepository()
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    first = service.generate("project-1", user)
    second = service.generate("project-1", user)

    # Same selection + inputs -> same deterministic id and a single Firestore doc.
    assert first.model_id == second.model_id
    assert len(projects.saved_documents) == 1


def test_generate_persists_stale_false():
    projects = FakeProjectRepository()
    service = GlobalUsageService(
        projects,
        FakeParameterResolver(),
        StaticUsageValueResolver(),
        FakeUsageModelService(),
    )
    user = UserOut(id="user-1", email="test@example.com", name="Test User")

    service.generate("project-1", user)

    assert projects.saved_documents[0]["stale"] is False
