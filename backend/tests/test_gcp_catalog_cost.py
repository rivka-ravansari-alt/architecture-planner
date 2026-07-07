"""End-to-end GCP catalog cost tests."""

from __future__ import annotations

import pytest

from app.pricing.gcp.project_pricing import calculate_project_gcp_sku_quantities
from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, ComponentPricingInput, UsageAssumption
from app.pricing_ingestion.models.documents import GcpCatalogRecord
from app.utils.slug import slugify
from tests.gcp_catalog_test_fixture import GcpCatalogTestFixture


def _assumption(key: str, value: int | float | str) -> UsageAssumption:
    return UsageAssumption(
        key=key,
        value=value,
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning="test",
    )


class TestGcpCatalogCost:
    def test_cloud_run_component_priced_from_catalog(self) -> None:
        fixture = GcpCatalogTestFixture()
        calculator = fixture.build_cost_calculator()
        inputs = [
            ComponentPricingInput(
                component_id="api",
                order=0,
                provider="gcp",
                cloud_service="Cloud Run",
                resolved=[
                    _assumption("requests_per_month", 3_000_000),
                    _assumption("avg_request_duration_seconds", 0.5),
                    _assumption("cpu", 1.0),
                    _assumption("memory_gb", 1.0),
                    _assumption("network_egress_gb", 1.0),
                    _assumption("min_instances", 0),
                ],
            )
        ]
        quantity_result = calculate_project_gcp_sku_quantities(inputs)
        model = get_gcp_pricing_model("Cloud Run")
        assert model is not None
        cost_result = calculator.calculate_project(
            quantity_result,
            {model.service: model},
        )
        assert cost_result.total_usd > 0
        assert cost_result.components[0].line_items

    def test_api_gateway_scales_per_million_requests(self) -> None:
        fixture = GcpCatalogTestFixture()
        fixture.repo.upsert(
            GcpCatalogRecord(
                id=slugify("API Gateway"),
                name="API Gateway",
                skus={
                    "requests": {
                        "sku_id": "manual-gcp-api-gateway-requests",
                        "description": "GCP API Gateway API calls",
                        "usage_unit": "1M requests",
                        "currency": "USD",
                        "unit_price_usd": 3.0,
                    },
                    "egress": {
                        "sku_id": "apigw-egress",
                        "description": "Network egress",
                        "usage_unit": "GiBy",
                        "currency": "USD",
                        "unit_price_usd": 0.19,
                    },
                },
                formula={
                    "requests_cost": "(requests / 1000000) * skus.requests.unit_price_usd",
                    "total": "requests_cost",
                },
            )
        )
        calculator = fixture.build_cost_calculator()
        inputs = [
            ComponentPricingInput(
                component_id="api_layer",
                order=0,
                provider="gcp",
                cloud_service="API Gateway",
                resolved=[
                    _assumption("requests_per_month", 1400),
                    _assumption("data_egress_gb", 2.4),
                ],
            )
        ]
        quantity_result = calculate_project_gcp_sku_quantities(inputs)
        model = get_gcp_pricing_model("API Gateway")
        assert model is not None
        cost_result = calculator.calculate_project(
            quantity_result,
            {model.service: model},
        )
        assert cost_result.total_usd < 1.0
        assert cost_result.total_usd != pytest.approx(3570.0)

        inputs_billable = [
            ComponentPricingInput(
                component_id="api_layer",
                order=0,
                provider="gcp",
                cloud_service="API Gateway",
                resolved=[
                    _assumption("requests_per_month", 3_500_000),
                    _assumption("data_egress_gb", 0),
                ],
            )
        ]
        billable_result = calculator.calculate_project(
            calculate_project_gcp_sku_quantities(inputs_billable),
            {model.service: model},
        )
        request_line = next(
            line for line in billable_result.components[0].line_items if line.sku_key == "requests"
        )
        assert request_line.monthly_cost_usd == pytest.approx(4.5, abs=0.01)
