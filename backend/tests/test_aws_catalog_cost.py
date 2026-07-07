"""End-to-end AWS catalog cost tests."""

from __future__ import annotations

from app.pricing.aws.project_pricing import calculate_project_aws_sku_quantities
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, ComponentPricingInput, UsageAssumption
from tests.aws_catalog_test_fixture import AwsCatalogTestFixture


def _assumption(key: str, value: int | float | str) -> UsageAssumption:
    return UsageAssumption(
        key=key,
        value=value,
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning="test",
    )


class TestAwsCatalogCost:
    def test_lambda_component_priced_from_catalog(self) -> None:
        fixture = AwsCatalogTestFixture()
        calculator = fixture.build_cost_calculator()
        inputs = [
            ComponentPricingInput(
                component_id="api",
                order=0,
                provider="aws",
                cloud_service="Lambda",
                resolved=[
                    _assumption("executions_per_month", 2_000_000),
                    _assumption("avg_execution_duration_ms", 500),
                    _assumption("memory_mb", 1024),
                    _assumption("network_egress_gb", 1.0),
                ],
            )
        ]
        quantity_result = calculate_project_aws_sku_quantities(inputs)
        model = get_aws_pricing_model("Lambda")
        assert model is not None
        cost_result = calculator.calculate_project(
            quantity_result,
            {model.service: model},
        )
        assert cost_result.total_usd > 0
        assert cost_result.components[0].line_items

    def test_appconfig_does_not_price_experiment_hours(self) -> None:
        fixture = AwsCatalogTestFixture()
        calculator = fixture.build_cost_calculator()
        inputs = [
            ComponentPricingInput(
                component_id="config",
                order=0,
                provider="aws",
                cloud_service="AppConfig",
                resolved=[
                    _assumption("configurations_count", 1),
                    _assumption("deployment_events_per_month", 40),
                ],
            )
        ]
        quantity_result = calculate_project_aws_sku_quantities(inputs)
        model = get_aws_pricing_model("AppConfig")
        assert model is not None
        cost_result = calculator.calculate_project(
            quantity_result,
            {model.service: model},
        )
        assert cost_result.total_usd < 5.0
        priced_roles = {line.catalog_role for line in cost_result.components[0].line_items}
        assert "use1_appconfig_experimenthours" not in priced_roles
