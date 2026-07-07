"""Tests for Azure SKU quantity calculators."""

from __future__ import annotations

import pytest

from app.pricing import (
    calculate_azure_sku_quantities,
    get_azure_pricing_model,
    resolve_usage_assumptions,
)
from app.pricing.azure.sku_quantities._helpers import MONTHLY_SECONDS


def _quantity(result, sku_key: str):
    return next(item for item in result.quantities if item.sku_key == sku_key)


@pytest.mark.parametrize(
    "service_name",
    [
        "Azure Container Apps",
        "Azure Functions",
        "Azure Blob Storage",
        "Azure SQL Database",
        "Azure Queue Storage",
        "Azure Service Bus",
    ],
)
def test_missing_required_inputs_returns_missing_not_quantities(service_name: str) -> None:
    model = get_azure_pricing_model(service_name)
    assert model is not None

    result = calculate_azure_sku_quantities(model, resolved=[])

    assert result.ready is False
    assert result.quantities == []
    assert result.missing


@pytest.mark.parametrize(
    "service_name",
    [
        "Azure Container Apps",
        "Azure Functions",
        "Azure Blob Storage",
        "Azure SQL Database",
        "Azure Queue Storage",
        "Azure Service Bus",
    ],
)
def test_all_quantities_have_metadata(service_name: str) -> None:
    model = get_azure_pricing_model(service_name)
    assert model is not None

    user_provided = _sample_user_inputs(service_name)
    resolution = resolve_usage_assumptions(model, user_provided=user_provided)
    assert resolution.ready_for_calculation is True

    result = calculate_azure_sku_quantities(model, resolution.resolved)
    assert result.ready is True
    assert result.quantities

    for quantity in result.quantities:
        assert quantity.sku_key
        assert quantity.quantity >= 0
        assert quantity.unit
        assert quantity.formula
        assert quantity.input_values_used is not None
        assert quantity.free_tier_applied is False


def _sample_user_inputs(service_name: str) -> dict:
    samples = {
        "Azure Container Apps": {
            "requests_per_month": 1_000_000,
            "network_egress_gb": 25,
        },
        "Azure Functions": {
            "executions_per_month": 2_000_000,
            "network_egress_gb": 10,
        },
        "Azure Blob Storage": {
            "storage_gb": 500,
            "write_operations": 100_000,
            "read_operations": 250_000,
            "list_operations": 50_000,
            "data_egress_gb": 80,
        },
        "Azure SQL Database": {
            "tier": "Standard S1",
            "storage_gb": 300,
            "backup_storage_gb": 50,
        },
        "Azure Queue Storage": {
            "queue_operations": 5_000_000,
            "storage_gb": 2,
            "data_egress_gb": 5,
        },
        "Azure Service Bus": {
            "messaging_tier": "Standard",
            "queue_operations": 20_000_000,
            "brokered_connections": 1500,
        },
    }
    return samples[service_name]


class TestContainerAppsQuantities:
    def test_activity_only_when_scale_to_zero(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "requests_per_month": 1_000_000,
                "avg_request_duration_seconds": 0.5,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 0,
                "min_replicas": 0,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "requests").quantity == 1_000_000
        assert _quantity(result, "vcpu_seconds").quantity == 250_000
        assert _quantity(result, "memory_gb_seconds").quantity == 500_000
        assert _quantity(result, "network_egress_gb").quantity == 0

    def test_min_replicas_baseline_wins(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "requests_per_month": 100_000,
                "avg_request_duration_seconds": 0.25,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 5,
                "min_replicas": 1,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        expected_baseline_vcpu = 1 * 0.5 * MONTHLY_SECONDS
        expected_baseline_memory = 1 * 1.0 * MONTHLY_SECONDS

        assert _quantity(result, "vcpu_seconds").quantity == expected_baseline_vcpu
        assert _quantity(result, "memory_gb_seconds").quantity == expected_baseline_memory
        assert _quantity(result, "vcpu_seconds").warnings


class TestFunctionsQuantities:
    def test_execution_time_gb_seconds_formula(self) -> None:
        model = get_azure_pricing_model("Azure Functions")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"executions_per_month": 1_000_000},
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        # 1_000_000 * (200/1000) * (512/1024) = 100_000
        assert _quantity(result, "executions").quantity == 1_000_000
        assert _quantity(result, "execution_time_gb_seconds").quantity == pytest.approx(100_000)
        assert _quantity(result, "execution_time_gb_seconds").formula == (
            "executions_per_month * (avg_execution_duration_ms / 1000) * (memory_mb / 1024)"
        )

    def test_premium_plan_uses_vcpu_hours(self) -> None:
        model = get_azure_pricing_model("Azure Functions")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "plan": "premium",
                "executions_per_month": 1_000_000,
                "avg_execution_duration_ms": 3600,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        sku_keys = {item.sku_key for item in result.quantities}
        assert "vcpu_hours" in sku_keys
        assert "executions" not in sku_keys
        assert "execution_time_gb_seconds" not in sku_keys
        assert _quantity(result, "vcpu_hours").quantity == pytest.approx(1_000)


class TestBlobStorageQuantities:
    def test_all_operation_skus_mapped(self) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "storage_gb": 120,
                "write_operations": 10_000,
                "read_operations": 20_000,
                "list_operations": 5_000,
                "data_egress_gb": 15,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "storage_gb_month").quantity == 120
        assert _quantity(result, "write_operations").quantity == 10_000
        assert _quantity(result, "read_operations").quantity == 20_000
        assert _quantity(result, "list_operations").quantity == 5_000
        assert _quantity(result, "network_egress_gb").quantity == 15

    def test_retrieval_gb_when_cool_tier_reads(self) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "storage_gb": 50,
                "access_tier": "Cool",
                "redundancy": "LRS",
                "data_retrieval_gb": 12,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "retrieval_gb").quantity == 12


class TestSqlDatabaseQuantities:
    def test_included_storage_not_double_counted(self) -> None:
        model = get_azure_pricing_model("Azure SQL Database")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"tier": "Standard S1", "storage_gb": 300},
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "database_instance_months").quantity == 1
        assert _quantity(result, "storage_gb_month").quantity == 50
        assert result.included_usage
        assert result.included_usage[0].quantity == 250

    def test_vcore_tier_bills_all_storage(self) -> None:
        model = get_azure_pricing_model("Azure SQL Database")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"tier": "General Purpose", "storage_gb": 64},
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "storage_gb_month").quantity == 64

    def test_backup_storage_when_provided(self) -> None:
        model = get_azure_pricing_model("Azure SQL Database")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "tier": "General Purpose",
                "storage_gb": 32,
                "backup_storage_gb": 100,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "backup_storage_gb_month").quantity == 100


class TestQueueStorageQuantities:
    def test_storage_omitted_when_zero(self) -> None:
        model = get_azure_pricing_model("Azure Queue Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"queue_operations": 1_000_000, "storage_gb": 0},
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        sku_keys = {item.sku_key for item in result.quantities}
        assert "queue_operations" in sku_keys
        assert "storage_gb_month" not in sku_keys

    def test_egress_when_provided(self) -> None:
        model = get_azure_pricing_model("Azure Queue Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "queue_operations": 1_000_000,
                "storage_gb": 1,
                "data_egress_gb": 3.5,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "network_egress_gb").quantity == pytest.approx(3.5)


class TestServiceBusQuantities:
    def test_standard_tier_base_and_operations(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "messaging_tier": "Standard",
                "queue_operations": 5_000_000,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "base_units_month").quantity == 1
        assert _quantity(result, "base_units_month").unit == "namespace-months"
        assert _quantity(result, "operations").quantity == 5_000_000

    def test_standard_brokered_connections_above_included(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "messaging_tier": "Standard",
                "queue_operations": 1_000_000,
                "brokered_connections": 1500,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "brokered_connections").quantity == 500

    def test_premium_tier_mu_hours(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "messaging_tier": "Premium",
                "messaging_units": 2,
                "queue_operations": 0,
            },
        )
        result = calculate_azure_sku_quantities(model, resolution.resolved)

        assert _quantity(result, "messaging_unit_hours").unit == "MU-hours/month"
        assert _quantity(result, "messaging_unit_hours").quantity == pytest.approx(2 * 730)
        assert "base_units_month" not in {item.sku_key for item in result.quantities}
