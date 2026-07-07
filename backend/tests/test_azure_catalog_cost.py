"""Tests for Azure catalog price lookup and cost calculation."""

from __future__ import annotations

import pytest

from app.pricing import (
    ComponentPricingInput,
    FreeTierPoolState,
    apply_project_free_tier,
    calculate_azure_sku_quantities,
    calculate_project_azure_sku_quantities,
    get_azure_pricing_model,
    resolve_usage_assumptions,
)
from app.pricing.azure.meter_scaling import MeterUnitScaler
from app.pricing.azure.sku_roles import SkuRoleResolver
from app.pricing.schemas import ComponentSkuResult
from tests.azure_catalog_test_fixture import AzureCatalogTestFixture


def _adjusted(model, user_provided: dict) -> ComponentSkuResult:
    resolution = resolve_usage_assumptions(model, user_provided=user_provided)
    raw = calculate_azure_sku_quantities(model, resolution.resolved)
    pool = FreeTierPoolState()
    adjusted = apply_project_free_tier(model, raw, pool, resolved=resolution.resolved)
    return ComponentSkuResult(
        component_id="test",
        service=adjusted.service,
        quantities=adjusted.quantities,
        included_usage=adjusted.included_usage,
        missing=adjusted.missing,
        ready=adjusted.ready,
        resolved=resolution.resolved,
        warnings=adjusted.warnings,
    )


class TestSkuRoleResolver:
    def test_functions_gb_seconds_maps_to_memory(self) -> None:
        model = get_azure_pricing_model("Azure Functions")
        resolver = SkuRoleResolver()
        assert resolver.resolve(model, "execution_time_gb_seconds") == ["memory"]

    def test_service_bus_operations_maps_to_queue(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolver = SkuRoleResolver()
        assert resolver.resolve(model, "operations") == ["queue"]

    def test_service_bus_premium_mu_maps_to_cpu(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolver = SkuRoleResolver()
        assert resolver.resolve(model, "messaging_unit_hours") == ["cpu"]

    def test_blob_list_operations_maps_to_requests(self) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        resolver = SkuRoleResolver()
        assert resolver.resolve(model, "list_operations") == ["requests"]


class TestMeterUnitScaler:
    def test_per_10k_operations(self) -> None:
        scaler = MeterUnitScaler()
        result = scaler.scale(10_000, "operations/month", "10 K")
        assert result is not None
        assert result[0] == pytest.approx(1.0)

    def test_gb_month_direct(self) -> None:
        scaler = MeterUnitScaler()
        result = scaler.scale(115, "GB-months", "1 GB/Month")
        assert result is not None
        assert result[0] == pytest.approx(115)


class TestAzureCostCalculator:
    @pytest.fixture
    def calculator(self):
        return AzureCatalogTestFixture().build_cost_calculator()

    def test_functions_execution_and_memory_cost(self, calculator) -> None:
        model = get_azure_pricing_model("Azure Functions")
        component = _adjusted(model, {"executions_per_month": 5_000_000})
        result = calculator.calculate_component(model, component)

        executions = next(item for item in result.line_items if item.sku_key == "executions")
        gb_seconds = next(
            item for item in result.line_items if item.sku_key == "execution_time_gb_seconds"
        )
        assert executions.monthly_cost_usd == pytest.approx(0.8)
        assert gb_seconds.monthly_cost_usd == pytest.approx(0.1)

    def test_blob_hot_lrs_storage_after_free_tier(self, calculator) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        component = _adjusted(
            model,
            {"storage_gb": 120, "access_tier": "Hot", "redundancy": "LRS"},
        )
        result = calculator.calculate_component(model, component)

        storage = next(item for item in result.line_items if item.sku_key == "storage_gb_month")
        assert storage.quantity == pytest.approx(115)
        assert storage.monthly_cost_usd == pytest.approx(2.07)

    def test_container_apps_free_tier_vcpu_cost(self, calculator) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        component = _adjusted(
            model,
            {
                "requests_per_month": 1_800_000,
                "avg_request_duration_seconds": 1.0,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 0,
                "min_replicas": 0,
            },
        )
        result = calculator.calculate_component(model, component)

        vcpu = next(item for item in result.line_items if item.sku_key == "vcpu_seconds")
        assert vcpu.quantity == pytest.approx(720_000)
        assert vcpu.free_tier_applied is True
        assert vcpu.monthly_cost_usd == pytest.approx(720_000 * 0.000012)

    def test_sql_instance_and_storage_priced(self, calculator) -> None:
        model = get_azure_pricing_model("Azure SQL Database")
        component = _adjusted(model, {"tier": "Standard S1", "storage_gb": 300})
        result = calculator.calculate_component(model, component)

        instance = next(
            (item for item in result.line_items if item.sku_key == "database_instance_months"),
            None,
        )
        storage = next(item for item in result.line_items if item.sku_key == "storage_gb_month")
        assert instance is not None
        assert instance.monthly_cost_usd == pytest.approx(30.0)
        assert storage.quantity == pytest.approx(50)
        assert storage.monthly_cost_usd == pytest.approx(50 * 0.115)

    def test_blob_write_operations_per_10k_meter(self, calculator) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        component = _adjusted(
            model,
            {
                "storage_gb": 10,
                "access_tier": "Hot",
                "redundancy": "LRS",
                "write_operations": 25_000,
            },
        )
        result = calculator.calculate_component(model, component)

        writes = next(item for item in result.line_items if item.sku_key == "write_operations")
        assert writes.billable_units == pytest.approx(0.5)
        assert writes.monthly_cost_usd == pytest.approx(0.025)

    def test_project_total_sums_components(self, calculator) -> None:
        blob_model = get_azure_pricing_model("Azure Blob Storage")
        fn_model = get_azure_pricing_model("Azure Functions")

        blob_res = resolve_usage_assumptions(
            blob_model,
            user_provided={"storage_gb": 10, "access_tier": "Hot", "redundancy": "LRS"},
        )
        fn_res = resolve_usage_assumptions(
            fn_model,
            user_provided={"executions_per_month": 100_000},
        )
        qty_result = calculate_project_azure_sku_quantities(
            [
                ComponentPricingInput(
                    component_id="blob",
                    order=0,
                    azure_service="Azure Blob Storage",
                    resolved=blob_res.resolved,
                ),
                ComponentPricingInput(
                    component_id="fn",
                    order=1,
                    azure_service="Azure Functions",
                    resolved=fn_res.resolved,
                ),
            ]
        )
        cost_result = calculator.calculate_project(
            qty_result,
            {
                "Azure Blob Storage": blob_model,
                "Azure Functions": fn_model,
            },
        )
        assert cost_result.total_usd == pytest.approx(
            sum(c.subtotal_usd for c in cost_result.components)
        )
        assert len(cost_result.components) == 2


class TestAzureCatalogLookup:
    def test_lookup_by_catalog_service_name(self) -> None:
        fixture = AzureCatalogTestFixture()
        lookup = fixture.build_cost_calculator()._catalog_lookup  # noqa: SLF001
        price = lookup.get_unit_price("Blob Storage", "storage")
        assert price is not None
        assert price.unit_price_usd == pytest.approx(0.018)
