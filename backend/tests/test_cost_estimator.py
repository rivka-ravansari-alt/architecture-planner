"""Tests for deterministic cost estimation."""

from __future__ import annotations

from app.schemas.cost import UsageProfile
from app.schemas.domain import MappedComponent
from app.services.cloud_infrastructure_cost_service import CloudInfrastructureCostService
from app.services.cost_estimator_service import CostEstimatorService


def _component(
    *,
    key: str,
    component_type: str,
    cloud: dict[str, list[str]],
    optional: bool = False,
) -> MappedComponent:
    return MappedComponent(
        key=key,
        name=key,
        component_type=component_type,
        reason="test",
        category="core",
        optional=optional,
        order=0,
        cloud=cloud,
        implementation_options={},
    )


def test_minimal_architecture_produces_detailed_cloud_infrastructure():
    components = [
        _component(
            key="api_layer",
            component_type="api_gateway",
            cloud={
                "aws": ["API Gateway", "Lambda"],
                "gcp": ["API Gateway", "Cloud Run"],
                "azure": ["API Management", "Azure Functions"],
            },
        ),
        _component(
            key="database",
            component_type="database",
            cloud={
                "aws": ["RDS"],
                "gcp": ["Cloud SQL"],
                "azure": ["Azure SQL Database"],
            },
        ),
    ]
    usage = UsageProfile(expected_users="100", stage="mvp")

    result = CostEstimatorService().estimate(components=components, usage=usage)

    assert set(result.cloud_cost) == {"aws", "gcp", "azure"}
    assert result.cloud_cost["aws"].low > 0
    assert "database" in result.cloud_infrastructure.categories
    assert result.cloud_infrastructure.provider_totals["aws"].low > 0
    assert result.ai_services_cost == {}
    assert result.external_services_cost == {}
    assert result.assumptions
    assert result.confidence in {"low", "medium", "high"}


def test_cloud_infrastructure_categories_compare_providers_side_by_side():
    components = [
        _component(
            key="api_layer",
            component_type="api_gateway",
            cloud={
                "aws": ["API Gateway"],
                "gcp": ["API Gateway"],
                "azure": ["API Management"],
            },
        ),
        _component(
            key="object_storage",
            component_type="object_storage",
            cloud={
                "aws": ["S3"],
                "gcp": ["Cloud Storage"],
                "azure": ["Blob Storage"],
            },
        ),
    ]
    usage = UsageProfile(
        expected_users="1000",
        file_uploads=True,
        files_per_month="1k_10k",
        average_file_size="medium",
    )

    infra = CloudInfrastructureCostService().estimate(components, usage)

    storage = infra.categories["storage"]
    assert storage.aws.low > 0
    assert storage.gcp.low > 0
    assert storage.azure.low > 0
    assert infra.provider_totals["aws"].low >= storage.aws.low


def test_file_uploads_increase_storage_category_costs():
    base_components = [
        _component(
            key="object_storage",
            component_type="object_storage",
            cloud={"aws": ["S3"], "gcp": ["Cloud Storage"], "azure": ["Blob Storage"]},
        )
    ]
    light_usage = UsageProfile(
        file_uploads=True,
        files_per_month="under_1k",
        average_file_size="small",
    )
    heavy_usage = UsageProfile(
        file_uploads=True,
        files_per_month="10k_plus",
        average_file_size="large",
    )

    estimator = CloudInfrastructureCostService()
    light = estimator.estimate(base_components, light_usage)
    heavy = estimator.estimate(base_components, heavy_usage)

    assert heavy.categories["storage"].aws.high > light.categories["storage"].aws.high


def test_ai_usage_adds_rough_placeholder_only():
    components = [
        _component(
            key="ai_service",
            component_type="ai_provider",
            cloud={
                "aws": ["Bedrock"],
                "gcp": ["Vertex AI"],
                "azure": ["Azure OpenAI Service"],
            },
        )
    ]
    usage = UsageProfile(ai=True)

    result = CostEstimatorService().estimate(components=components, usage=usage)

    assert "ai_services" in result.ai_services_cost
    assert "anthropic" not in result.ai_services_cost
    assert any("rough placeholder" in item for item in result.unknown_items)


def test_notifications_and_payments_add_rough_external_placeholder():
    usage = UsageProfile(notifications=True, payments=True)

    result = CostEstimatorService().estimate(
        components=[
            _component(
                key="api_layer",
                component_type="api_gateway",
                cloud={"aws": ["API Gateway"], "gcp": ["API Gateway"], "azure": ["API Management"]},
            )
        ],
        usage=usage,
    )

    assert "external_services" in result.external_services_cost
    assert any("rough placeholder" in item for item in result.unknown_items)


def test_production_stage_increases_cloud_estimates():
    components = [
        _component(
            key="api_layer",
            component_type="api_gateway",
            cloud={"aws": ["API Gateway"], "gcp": ["API Gateway"], "azure": ["API Management"]},
        )
    ]
    mvp = UsageProfile(stage="mvp")
    production = UsageProfile(stage="production")

    estimator = CostEstimatorService()
    mvp_result = estimator.estimate(components=components, usage=mvp)
    prod_result = estimator.estimate(components=components, usage=production)

    assert prod_result.cloud_cost["aws"].high >= mvp_result.cloud_cost["aws"].high


def test_optional_components_are_excluded_from_costs():
    components = [
        _component(
            key="object_storage",
            component_type="object_storage",
            cloud={"aws": ["S3"], "gcp": ["Cloud Storage"], "azure": ["Blob Storage"]},
            optional=True,
        )
    ]
    usage = UsageProfile(file_uploads=True)

    result = CostEstimatorService().estimate(components=components, usage=usage)

    assert result.cloud_cost["aws"].low == 0
    assert result.cloud_infrastructure.categories == {}


def test_observability_categories_detected_from_services():
    components = [
        _component(
            key="monitoring",
            component_type="monitoring",
            cloud={
                "aws": ["CloudWatch"],
                "gcp": ["Cloud Monitoring"],
                "azure": ["Azure Monitor"],
            },
        ),
        _component(
            key="logging",
            component_type="logging",
            cloud={
                "aws": ["CloudWatch Logs"],
                "gcp": ["Cloud Logging"],
                "azure": ["Log Analytics"],
            },
        ),
    ]

    infra = CloudInfrastructureCostService().estimate(components, UsageProfile(stage="production"))

    assert "monitoring" in infra.categories
    assert "logging" in infra.categories


def test_high_confidence_with_complete_intake_data():
    usage = UsageProfile(
        expected_users="1000",
        stage="production",
        file_uploads=True,
        files_per_month="1k_10k",
        average_file_size="medium",
        real_time=True,
        real_time_types=["live_chat"],
        has_intake_features=True,
        explicit_fields=frozenset(
            {
                "expected_users",
                "stage",
                "file_uploads",
                "files_per_month",
                "average_file_size",
                "real_time",
                "real_time_types",
            }
        ),
    )

    result = CostEstimatorService().estimate(
        components=[
            _component(
                key="api_layer",
                component_type="api_gateway",
                cloud={
                    "aws": ["API Gateway"],
                    "gcp": ["API Gateway"],
                    "azure": ["API Management"],
                },
            )
        ],
        usage=usage,
    )

    assert result.confidence == "high"
