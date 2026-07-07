"""Tests for shared LLM usage inference across providers."""

from __future__ import annotations

from app.core.exceptions import AIClientError
from app.models import Project, RequirementAnswers
from app.pricing.schemas import AssumptionConfidence, AssumptionSource
from app.pricing.usage.service import UsageAssumptionsService
from app.services.component_mapper_service import ComponentMapperService
from app.services.generation_service import GenerationService
from app.config.params import WORKFLOW_STATUS_ARCHITECTURE_APPROVED
from tests.conftest import MockAIClient
from tests.fixtures import VALID_AI_RESPONSE_JSON
from tests.shared_usage_assumptions_fixtures import shared_usage_assumptions_json
from app.schemas.domain import MappedComponent


def _project(*, expected_users: str = "1000") -> Project:
    return Project(
        name="TaskFlow",
        description="Team task management SaaS",
        expected_users=expected_users,
        stage="mvp",
        architecture_summary="Web API with optional file uploads.",
    )


def _taskflow_components() -> list[MappedComponent]:
    return [
        MappedComponent(
            key="web_client",
            name="Web Client",
            component_type="web_app",
            reason="Browser UI",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Amplify Hosting", "gcp": "Firebase Hosting", "azure": "Azure App Service"},
        ),
        MappedComponent(
            key="api_gateway",
            name="Backend / API Layer",
            component_type="api",
            reason="API entry point",
            category="core",
            optional=False,
            order=1,
            cloud={"aws": "API Gateway", "gcp": "API Gateway", "azure": "API Management"},
        ),
        MappedComponent(
            key="object_storage",
            name="Object Storage",
            component_type="object_storage",
            reason="Uploaded files",
            category="optional",
            optional=True,
            order=3,
            cloud={"aws": "S3", "gcp": "Cloud Storage", "azure": "Blob Storage"},
        ),
    ]


class TestSharedUsageInference:
    def test_shared_llm_maps_to_all_providers(self) -> None:
        service = UsageAssumptionsService()
        project = _project()
        components = _taskflow_components()
        feature_flags = {"file_upload": True, "ai": False, "background_processing": False}

        shared = service.parse_shared_response(
            shared_usage_assumptions_json(),
            project,
            components,
            feature_flags=feature_flags,
        )
        assert shared.inference_source == "llm"

        provider_results = service.map_shared_to_providers(
            shared,
            project=project,
            components=components,
            feature_flags=feature_flags,
        )

        for provider in ("azure", "aws", "gcp"):
            result = provider_results[provider]
            assert result.inference_source == "llm", provider
            assert result.components, provider
            for assumption in result.components[0].resolved:
                assert assumption.source == AssumptionSource.inferred
                assert assumption.confidence != AssumptionConfidence.low

    def test_shared_prompt_is_provider_neutral(self) -> None:
        service = UsageAssumptionsService()
        prompt = service.build_shared_prompt(_project(), _taskflow_components())
        assert "sessions_per_user_per_month" in prompt
        assert "azure_service" not in prompt
        assert "aws_service" not in prompt
        assert "component_type: web_app" in prompt

    def test_invalid_shared_response_falls_back_per_provider(self) -> None:
        service = UsageAssumptionsService()
        project = _project()
        components = _taskflow_components()
        fallback = service.infer_all_providers_heuristic(
            project,
            components,
            inference_source="heuristic_fallback",
        )
        for provider in ("azure", "aws", "gcp"):
            assert fallback[provider].inference_source == "heuristic_fallback"
            assert fallback[provider].components


class RoutingMockAIClient(MockAIClient):
    def __init__(
        self,
        *,
        architecture_response: str = VALID_AI_RESPONSE_JSON,
        usage_response: str | None = None,
    ) -> None:
        super().__init__(architecture_response)
        self._usage_response = usage_response or shared_usage_assumptions_json()
        self.usage_prompt_seen = False

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        if "Infer realistic per-user usage behavior" in prompt:
            self.usage_prompt_seen = True
            return self._usage_response
        return super().generate(prompt, system_prompt=system_prompt)


class FailingUsageMockAIClient(RoutingMockAIClient):
    def generate(self, prompt: str, *, system_prompt: str | None = None) -> str:
        if "Infer realistic per-user usage behavior" in prompt:
            raise AIClientError("usage inference unavailable")
        return super().generate(prompt, system_prompt=system_prompt)


def _approved_project_with_components(db_session, test_user):
    from app.models import Project, ProjectComponent, CloudMapping

    project = Project(
        user_id=test_user.id,
        name="TaskFlow",
        description="Team task management SaaS",
        project_types=["web_app"],
        stage="mvp",
        expected_users="1000",
        workflow_status=WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        architecture_summary="Web API with optional uploads.",
    )
    project.answers = RequirementAnswers(
        auth=True,
        file_upload=True,
        background_processing=False,
        dashboards=False,
        ai=False,
        payments=False,
        include_edge_cases=False,
    )
    components = _taskflow_components()
    for mapped in components:
        component = ProjectComponent(
            key=mapped.key,
            name=mapped.name,
            component_type=mapped.component_type,
            reason=mapped.reason,
            category=mapped.category,
            optional=mapped.optional,
            order=mapped.order,
        )
        component.cloud_mapping = CloudMapping(
            aws=mapped.cloud["aws"],
            gcp=mapped.cloud["gcp"],
            azure=mapped.cloud["azure"],
        )
        project.components.append(component)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestGeneratePricingSharedLLM:
    def test_generate_pricing_uses_shared_llm_for_all_providers(
        self,
        db_session,
        test_user,
        catalog_service,
    ) -> None:
        ai_client = RoutingMockAIClient()
        project = _approved_project_with_components(db_session, test_user)
        mapper = ComponentMapperService(catalog_service)
        service = GenerationService(db_session, ai_client=ai_client, mapper=mapper)

        result = service.generate_pricing(project)

        assert ai_client.usage_prompt_seen
        assert result.workflow_status == "PRICING_GENERATED"
        assert len(result.cost_estimates) == 3
        for estimate in result.cost_estimates:
            detail = estimate.pricing_detail or {}
            assert detail.get("inference_source") == "llm", estimate.provider

    def test_generate_pricing_llm_failure_falls_back_all_providers(
        self,
        db_session,
        test_user,
        catalog_service,
    ) -> None:
        ai_client = FailingUsageMockAIClient()
        project = _approved_project_with_components(db_session, test_user)
        mapper = ComponentMapperService(catalog_service)
        service = GenerationService(db_session, ai_client=ai_client, mapper=mapper)

        result = service.generate_pricing(project)

        assert result.workflow_status == "PRICING_GENERATED"
        for estimate in result.cost_estimates:
            detail = estimate.pricing_detail or {}
            assert detail.get("inference_source") == "heuristic_fallback", estimate.provider

    def test_generate_pricing_invalid_shared_json_falls_back(
        self,
        db_session,
        test_user,
        catalog_service,
    ) -> None:
        ai_client = RoutingMockAIClient(usage_response='{"components": []}')
        project = _approved_project_with_components(db_session, test_user)
        mapper = ComponentMapperService(catalog_service)
        service = GenerationService(db_session, ai_client=ai_client, mapper=mapper)

        result = service.generate_pricing(project)

        for estimate in result.cost_estimates:
            detail = estimate.pricing_detail or {}
            assert detail.get("inference_source") == "heuristic_fallback", estimate.provider
