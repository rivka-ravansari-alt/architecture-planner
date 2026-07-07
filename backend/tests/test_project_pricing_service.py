"""Tests for ProjectPricingService orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.config.params import CLOUD_PROVIDERS, COST_CURRENCY
from app.models import Project
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.azure.project_costing import AzureProjectCostingPipeline
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.providers.heuristic import HeuristicProviderPricing
from app.pricing.schemas import (
    AssumptionConfidence,
    AssumptionSource,
    ComponentCostResult,
    ComponentPricingInput,
    ProjectAwsCostResult,
    ProjectAzureCostResult,
    ProjectGcpCostResult,
    UsageAssumption,
)
from app.schemas.domain import MappedComponent, ProviderCost
from app.services.component_mapper_service import ComponentMapperService
from app.services.project_pricing_service import ProjectPricingService


@pytest.fixture
def sample_project() -> Project:
    project = Project(
        name="Test",
        description="",
        stage="mvp",
        expected_users="100",
    )
    return project


@pytest.fixture
def sample_components() -> list[MappedComponent]:
    return [
        MappedComponent(
            key="api",
            name="API",
            component_type="service",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": "Functions"},
        ),
    ]


class TestProjectPricingService:
    def test_estimate_returns_all_providers(
        self,
        sample_project: Project,
        sample_components: list[MappedComponent],
    ) -> None:
        azure_pipeline = MagicMock(spec=AzureProjectCostingPipeline)
        azure_pipeline.calculate.return_value = ProjectAzureCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Azure Functions",
                    catalog_service_name="Functions",
                    subtotal_usd=42.50,
                )
            ],
            total_usd=42.50,
        )
        aws_pipeline = MagicMock(spec=AwsProjectCostingPipeline)
        aws_pipeline.calculate.return_value = ProjectAwsCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Lambda",
                    catalog_service_name="Lambda",
                    subtotal_usd=18.25,
                )
            ],
            total_usd=18.25,
        )
        gcp_pipeline = MagicMock(spec=GcpProjectCostingPipeline)
        gcp_pipeline.calculate.return_value = ProjectGcpCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Cloud Run",
                    catalog_service_name="Cloud Run",
                    subtotal_usd=22.10,
                )
            ],
            total_usd=22.10,
        )
        mapper = MagicMock(spec=ComponentMapperService)
        mapper.feature_flags_from_components.return_value = {
            "file_upload": False,
            "ai": False,
            "background_processing": False,
        }
        heuristic = HeuristicProviderPricing(mapper=mapper)
        service = ProjectPricingService(azure_pipeline, aws_pipeline, gcp_pipeline, heuristic)

        costs = service.estimate(sample_project, sample_components, mapper=mapper)

        assert len(costs) == len(CLOUD_PROVIDERS)
        azure = next(c for c in costs if c.provider == "azure")
        assert azure.monthly_low == pytest.approx(42.50)
        assert azure.monthly_high == pytest.approx(42.50)
        assert azure.currency == COST_CURRENCY
        assert "Catalog-based Azure" in azure.notes
        assert azure.pricing_detail is not None
        assert azure.pricing_detail["total_usd"] == pytest.approx(42.50)

        aws = next(c for c in costs if c.provider == "aws")
        assert aws.monthly_low == pytest.approx(18.25)
        assert aws.monthly_high == pytest.approx(18.25)
        assert "Catalog-based AWS" in aws.notes
        assert aws.pricing_detail is not None

        gcp = next(c for c in costs if c.provider == "gcp")
        assert gcp.monthly_low == pytest.approx(22.10)
        assert gcp.monthly_high == pytest.approx(22.10)
        assert "Catalog-based GCP" in gcp.notes
        assert gcp.pricing_detail is not None
        assert gcp.pricing_detail["total_usd"] == pytest.approx(22.10)

    def test_estimate_forwards_pricing_inputs(
        self,
        sample_project: Project,
        sample_components: list[MappedComponent],
    ) -> None:
        pricing_inputs = [
            ComponentPricingInput(
                component_id="api",
                order=0,
                provider="azure",
                cloud_service="Azure Functions",
                resolved=[
                    UsageAssumption(
                        key="executions_per_month",
                        value=10_000,
                        unit="executions/month",
                        source=AssumptionSource.inferred,
                        confidence=AssumptionConfidence.medium,
                        reasoning="Test fixture.",
                    )
                ],
            )
        ]
        aws_pricing_inputs = [
            ComponentPricingInput(
                component_id="api",
                order=0,
                provider="aws",
                cloud_service="Lambda",
                resolved=[
                    UsageAssumption(
                        key="executions_per_month",
                        value=10_000,
                        unit="executions/month",
                        source=AssumptionSource.inferred,
                        confidence=AssumptionConfidence.medium,
                        reasoning="Test fixture.",
                    )
                ],
            )
        ]
        azure_pipeline = MagicMock(spec=AzureProjectCostingPipeline)
        azure_pipeline.calculate.return_value = ProjectAzureCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Azure Functions",
                    catalog_service_name="Functions",
                    subtotal_usd=10.0,
                    resolved_assumptions=pricing_inputs[0].resolved,
                )
            ],
            total_usd=10.0,
        )
        aws_pipeline = MagicMock(spec=AwsProjectCostingPipeline)
        aws_pipeline.calculate.return_value = ProjectAwsCostResult(total_usd=5.0)
        gcp_pricing_inputs = [
            ComponentPricingInput(
                component_id="api",
                order=0,
                provider="gcp",
                cloud_service="Cloud Run",
                resolved=[
                    UsageAssumption(
                        key="requests_per_month",
                        value=10_000,
                        unit="requests/month",
                        source=AssumptionSource.inferred,
                        confidence=AssumptionConfidence.medium,
                        reasoning="Test fixture.",
                    )
                ],
            )
        ]
        gcp_pipeline = MagicMock(spec=GcpProjectCostingPipeline)
        gcp_pipeline.calculate.return_value = ProjectGcpCostResult(total_usd=7.0)
        mapper = MagicMock(spec=ComponentMapperService)
        mapper.feature_flags_from_components.return_value = {}
        service = ProjectPricingService(
            azure_pipeline,
            aws_pipeline,
            gcp_pipeline,
            HeuristicProviderPricing(mapper=mapper),
        )

        service.estimate(
            sample_project,
            sample_components,
            mapper=mapper,
            pricing_inputs=pricing_inputs,
            aws_pricing_inputs=aws_pricing_inputs,
            gcp_pricing_inputs=gcp_pricing_inputs,
            inference_source="llm",
        )

        azure_pipeline.calculate.assert_called_once()
        _, azure_kwargs = azure_pipeline.calculate.call_args
        assert azure_kwargs["pricing_inputs"] == pricing_inputs

        aws_pipeline.calculate.assert_called_once()
        _, aws_kwargs = aws_pipeline.calculate.call_args
        assert aws_kwargs["pricing_inputs"] == aws_pricing_inputs

        gcp_pipeline.calculate.assert_called_once()
        _, gcp_kwargs = gcp_pipeline.calculate.call_args
        assert gcp_kwargs["pricing_inputs"] == gcp_pricing_inputs

    def test_estimate_includes_inference_source_in_pricing_detail(
        self,
        sample_project: Project,
        sample_components: list[MappedComponent],
    ) -> None:
        azure_pipeline = MagicMock(spec=AzureProjectCostingPipeline)
        azure_pipeline.calculate.return_value = ProjectAzureCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Azure Functions",
                    catalog_service_name="Functions",
                    subtotal_usd=10.0,
                    resolved_assumptions=[
                        UsageAssumption(
                            key="executions_per_month",
                            value=10_000,
                            unit="executions/month",
                            source=AssumptionSource.inferred,
                            confidence=AssumptionConfidence.medium,
                            reasoning="Test.",
                        )
                    ],
                )
            ],
            total_usd=10.0,
        )
        aws_pipeline = MagicMock(spec=AwsProjectCostingPipeline)
        aws_pipeline.calculate.return_value = ProjectAwsCostResult(total_usd=5.0)
        gcp_pipeline = MagicMock(spec=GcpProjectCostingPipeline)
        gcp_pipeline.calculate.return_value = ProjectGcpCostResult(total_usd=7.0)
        mapper = MagicMock(spec=ComponentMapperService)
        mapper.feature_flags_from_components.return_value = {}
        service = ProjectPricingService(
            azure_pipeline,
            aws_pipeline,
            gcp_pipeline,
            HeuristicProviderPricing(mapper=mapper),
        )

        costs = service.estimate(
            sample_project,
            sample_components,
            mapper=mapper,
            inference_source="llm",
            aws_inference_source="heuristic_only",
            gcp_inference_source="heuristic_only",
        )

        azure = next(c for c in costs if c.provider == "azure")
        assert azure.pricing_detail is not None
        assert azure.pricing_detail["inference_source"] == "llm"
        assert azure.notes is not None
        assert "LLM-inferred" in azure.notes

        aws = next(c for c in costs if c.provider == "aws")
        assert aws.pricing_detail is not None
        assert aws.pricing_detail["inference_source"] == "heuristic_only"

        gcp = next(c for c in costs if c.provider == "gcp")
        assert gcp.pricing_detail is not None
        assert gcp.pricing_detail["inference_source"] == "heuristic_only"

    def test_gcp_uses_catalog_pipeline_not_heuristic(
        self,
        sample_project: Project,
        sample_components: list[MappedComponent],
    ) -> None:
        azure_pipeline = MagicMock(spec=AzureProjectCostingPipeline)
        azure_pipeline.calculate.return_value = ProjectAzureCostResult(total_usd=0.0)
        aws_pipeline = MagicMock(spec=AwsProjectCostingPipeline)
        aws_pipeline.calculate.return_value = ProjectAwsCostResult(total_usd=0.0)
        gcp_pipeline = MagicMock(spec=GcpProjectCostingPipeline)
        gcp_pipeline.calculate.return_value = ProjectGcpCostResult(
            components=[
                ComponentCostResult(
                    component_id="api",
                    service="Cloud Run",
                    catalog_service_name="Cloud Run",
                    subtotal_usd=15.0,
                    pricing_status="supported",
                )
            ],
            total_usd=15.0,
            supported_component_count=1,
        )
        mapper = MagicMock(spec=ComponentMapperService)
        mapper.feature_flags_from_components.return_value = {}
        heuristic = MagicMock(spec=HeuristicProviderPricing)
        service = ProjectPricingService(
            azure_pipeline,
            aws_pipeline,
            gcp_pipeline,
            heuristic,
        )

        costs = service.estimate(sample_project, sample_components, mapper=mapper)

        gcp_pipeline.calculate.assert_called_once()
        heuristic.estimate_provider.assert_not_called()
        gcp = next(c for c in costs if c.provider == "gcp")
        assert "Catalog-based GCP" in (gcp.notes or "")
        assert "Heuristic" not in (gcp.notes or "")
        assert gcp.monthly_low == pytest.approx(15.0)

    def test_heuristic_provider_estimate(self, sample_project: Project, sample_components) -> None:
        mapper = MagicMock(spec=ComponentMapperService)
        mapper.feature_flags_from_components.return_value = {
            "file_upload": True,
            "ai": False,
            "background_processing": False,
        }
        heuristic = HeuristicProviderPricing(mapper=mapper)
        result = heuristic.estimate_provider("gcp", sample_project, sample_components, mapper=mapper)
        assert isinstance(result, ProviderCost)
        assert result.provider == "gcp"
        assert "Heuristic" in result.notes
