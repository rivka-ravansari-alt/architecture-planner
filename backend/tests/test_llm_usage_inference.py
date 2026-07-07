"""Tests for LLM-based usage assumption inference."""

from __future__ import annotations

import json

import pytest

from app.core.exceptions import AIClientError, AIValidationError
from app.models import Project
from app.pricing.azure.heuristic_usage_inference import HeuristicUsageInference
from app.pricing.azure.llm_usage_inference import LLMUsageInferenceEngine
from app.pricing.schemas import AssumptionConfidence, AssumptionSource
from app.pricing.usage.scaling import scale_behavioral_assumptions
from app.schemas.domain import MappedComponent
from app.services.usage_assumptions_prompt_builder import UsageAssumptionsPromptBuilder
from app.validators.usage_assumptions_validator import UsageAssumptionsValidator
from tests.conftest import MockAIClient
from tests.usage_assumptions_fixtures import functions_usage_assumptions_json


def _project(*, expected_users: str = "100") -> Project:
    return Project(
        name="TaskFlow",
        description="Team task management SaaS",
        expected_users=expected_users,
        stage="mvp",
        architecture_summary="Web API with background workers and file uploads.",
    )


def _functions_component() -> MappedComponent:
    return MappedComponent(
        key="api",
        name="API",
        component_type="service",
        reason="HTTP API",
        category="core",
        optional=False,
        order=0,
        cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": "Functions"},
    )


class TestUsageAssumptionsPromptBuilder:
    def test_prompt_includes_product_context_and_per_user_guidance(self) -> None:
        prompt = UsageAssumptionsPromptBuilder().build(_project(), [_functions_component()])
        assert "TaskFlow" in prompt
        assert "Team task management SaaS" in prompt
        assert "sessions_per_user_per_month" in prompt
        assert "component_id: api" in prompt
        assert "ONE user" in prompt or "ONE typical user" in prompt
        assert "Do NOT multiply by user count" in prompt


class TestUsageAssumptionsValidator:
    def test_valid_response_scales_behavioral_to_billing_totals(self) -> None:
        validator = UsageAssumptionsValidator()
        result = validator.validate(
            functions_usage_assumptions_json(),
            [_functions_component()],
            project=_project(),
        )
        assert len(result) == 1
        executions = next(item for item in result[0].resolved if item.key == "executions_per_month")
        assert executions.value == 24_000
        assert "Scaled:" in executions.reasoning
        assert len(result[0].behavioral_assumptions) >= 3

    def test_scaling_uses_expected_user_count(self) -> None:
        validator = UsageAssumptionsValidator()
        result = validator.validate(
            functions_usage_assumptions_json(),
            [_functions_component()],
            project=_project(expected_users="1000"),
        )
        executions = next(item for item in result[0].resolved if item.key == "executions_per_month")
        assert executions.value == 240_000

    def test_missing_reasoning_is_rejected(self) -> None:
        payload = json.loads(functions_usage_assumptions_json())
        payload["components"][0]["assumptions"][0].pop("reasoning")
        validator = UsageAssumptionsValidator()
        with pytest.raises(AIValidationError, match="reasoning"):
            validator.validate(json.dumps(payload), [_functions_component()], project=_project())

    def test_missing_required_behavioral_key_is_rejected(self) -> None:
        payload = json.loads(functions_usage_assumptions_json())
        payload["components"][0]["assumptions"] = [
            item
            for item in payload["components"][0]["assumptions"]
            if item["key"] != "sessions_per_user_per_month"
        ]
        validator = UsageAssumptionsValidator()
        with pytest.raises(AIValidationError, match="sessions_per_user_per_month"):
            validator.validate(json.dumps(payload), [_functions_component()], project=_project())


class TestUsageScaling:
    def test_container_apps_scales_requests_and_egress(self) -> None:
        from app.pricing.schemas import UsageAssumption

        behavioral = {
            "sessions_per_user_per_month": UsageAssumption(
                key="sessions_per_user_per_month",
                value=10,
                unit="sessions/user/month",
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.high,
                reasoning="Daily exercise habit.",
            ),
            "requests_per_session": UsageAssumption(
                key="requests_per_session",
                value=30,
                unit="requests/session",
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.high,
                reasoning="CRUD per session.",
            ),
            "avg_response_size_kb": UsageAssumption(
                key="avg_response_size_kb",
                value=300,
                unit="KB/request",
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.medium,
                reasoning="JSON dashboard payloads.",
            ),
        }
        scaled = scale_behavioral_assumptions(
            "Azure Container Apps",
            behavioral=behavioral,
            config={},
            expected_users=10_000,
        )
        assert scaled["requests_per_month"].value == 3_000_000
        assert scaled["network_egress_gb"].value > 0


class TestLLMUsageInferenceEngine:
    def test_llm_success_returns_inferred_inputs(self) -> None:
        engine = LLMUsageInferenceEngine(
            ai_client=MockAIClient(functions_usage_assumptions_json()),
        )
        inputs, _, raw = engine.infer_components(_project(), [_functions_component()])
        assert raw is not None
        assert len(inputs) == 1
        assert all(item.source == AssumptionSource.inferred for item in inputs[0].resolved)
        assert inputs[0].behavioral_assumptions

    def test_llm_failure_falls_back_to_heuristic(self) -> None:
        class FailingClient(MockAIClient):
            def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
                raise AIClientError("network down")

        engine = LLMUsageInferenceEngine(ai_client=FailingClient())
        inputs, _, raw = engine.infer_components(_project(), [_functions_component()])
        assert raw is None
        assert len(inputs) == 1
        executions = next(item for item in inputs[0].resolved if item.key == "executions_per_month")
        assert executions.confidence == AssumptionConfidence.low
        assert executions.reasoning

    def test_invalid_llm_response_falls_back_to_heuristic(self) -> None:
        engine = LLMUsageInferenceEngine(ai_client=MockAIClient('{"components": []}'))
        inputs, _, raw = engine.infer_components(_project(), [_functions_component()])
        assert raw is None
        assert len(inputs) == 1
        assert all(item.confidence == AssumptionConfidence.low for item in inputs[0].resolved)


class TestHeuristicUsageInference:
    def test_heuristic_tags_inferred_low_confidence(self) -> None:
        heuristic = HeuristicUsageInference()
        inputs = heuristic.infer_components(_project(), [_functions_component()])
        assert len(inputs) == 1
        for assumption in inputs[0].resolved:
            assert assumption.source == AssumptionSource.inferred
            assert assumption.confidence == AssumptionConfidence.low
            assert assumption.reasoning
