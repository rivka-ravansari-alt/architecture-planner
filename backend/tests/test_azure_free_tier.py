"""Tests for Azure subscription free-tier pooling and deductions."""

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


def _quantity(result, sku_key: str):
    return next(item for item in result.quantities if item.sku_key == sku_key)


def _apply(model, resolved):
    raw = calculate_azure_sku_quantities(model, resolved)
    pool = FreeTierPoolState()
    return apply_project_free_tier(model, raw, pool, resolved=resolved), pool


class TestContainerAppsFreeTier:
    def test_vcpu_seconds_deduction(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "requests_per_month": 1_800_000,
                "avg_request_duration_seconds": 1.0,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 0,
                "min_replicas": 0,
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        vcpu = _quantity(adjusted, "vcpu_seconds")
        assert vcpu.raw_quantity == pytest.approx(900_000)
        assert vcpu.free_tier_deducted == pytest.approx(180_000)
        assert vcpu.quantity == pytest.approx(720_000)
        assert vcpu.free_tier_applied is True

    def test_min_replicas_skips_free_tier(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "requests_per_month": 1_000_000,
                "avg_request_duration_seconds": 0.5,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 0,
                "min_replicas": 1,
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        vcpu = _quantity(adjusted, "vcpu_seconds")
        assert vcpu.free_tier_applied is False
        assert vcpu.free_tier_deducted == 0
        assert any("min_replicas=0" in warning for warning in adjusted.warnings)


class TestProjectFreeTierPool:
    def test_two_container_apps_share_requests_grant(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        assert model is not None

        def make_component(component_id: str, order: int, requests: int) -> ComponentPricingInput:
            resolution = resolve_usage_assumptions(
                model,
                user_provided={
                    "requests_per_month": requests,
                    "avg_request_duration_seconds": 0.25,
                    "cpu": 0.5,
                    "memory_gb": 1.0,
                    "network_egress_gb": 0,
                    "min_replicas": 0,
                },
            )
            return ComponentPricingInput(
                component_id=component_id,
                order=order,
                azure_service="Azure Container Apps",
                resolved=resolution.resolved,
            )

        project = calculate_project_azure_sku_quantities(
            [
                make_component("app-a", 0, 1_500_000),
                make_component("app-b", 1, 1_000_000),
            ]
        )

        first = next(item for item in project.components if item.component_id == "app-a")
        second = next(item for item in project.components if item.component_id == "app-b")

        first_requests = _quantity(first, "requests")
        second_requests = _quantity(second, "requests")

        assert first_requests.raw_quantity == 1_500_000
        assert first_requests.free_tier_deducted == 1_500_000
        assert first_requests.quantity == 0

        assert second_requests.raw_quantity == 1_000_000
        assert second_requests.free_tier_deducted == 500_000
        assert second_requests.quantity == 500_000

        pool = project.pool_summary["azure_container_apps_consumption"]
        assert pool["initial"]["requests"] == 2_000_000
        assert pool["remaining"]["requests"] == 0


class TestFunctionsFreeTier:
    def test_execution_time_gb_seconds_mapping(self) -> None:
        model = get_azure_pricing_model("Azure Functions")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"executions_per_month": 1_000_000},
        )
        adjusted, _ = _apply(model, resolution.resolved)

        gb_seconds = _quantity(adjusted, "execution_time_gb_seconds")
        assert gb_seconds.raw_quantity == pytest.approx(100_000)
        assert gb_seconds.free_tier_deducted == pytest.approx(100_000)
        assert gb_seconds.quantity == pytest.approx(0)
        assert gb_seconds.free_tier_applied is True


class TestBlobStorageFreeTier:
    def test_hot_lrs_storage_deduction(self) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "storage_gb": 120,
                "access_tier": "Hot",
                "redundancy": "LRS",
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        storage = _quantity(adjusted, "storage_gb_month")
        assert storage.raw_quantity == 120
        assert storage.free_tier_deducted == 5
        assert storage.quantity == 115
        assert storage.free_tier_applied is True

    def test_cool_tier_skips_free_tier(self) -> None:
        model = get_azure_pricing_model("Azure Blob Storage")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "storage_gb": 120,
                "access_tier": "Cool",
                "redundancy": "LRS",
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        storage = _quantity(adjusted, "storage_gb_month")
        assert storage.quantity == 120
        assert storage.free_tier_applied is False
        assert any("Hot LRS" in warning for warning in adjusted.warnings)


class TestSqlDatabaseFreeTier:
    def test_tier_inclusion_only_no_subscription_free_tier(self) -> None:
        model = get_azure_pricing_model("Azure SQL Database")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={"tier": "Standard S1", "storage_gb": 300},
        )
        adjusted, _ = _apply(model, resolution.resolved)

        storage = _quantity(adjusted, "storage_gb_month")
        assert storage.raw_quantity == 300
        assert storage.quantity == 50
        assert storage.free_tier_applied is False
        assert storage.free_tier_deducted == 0

        tier_included = [item for item in adjusted.included_usage if item.source == "tier"]
        assert tier_included
        assert tier_included[0].quantity == 250
        assert not any(item.source == "free_tier" for item in adjusted.included_usage)


class TestServiceBusFreeTier:
    def test_standard_operations_deduction(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "messaging_tier": "Standard",
                "queue_operations": 20_000_000,
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        operations = _quantity(adjusted, "operations")
        assert operations.raw_quantity == 20_000_000
        assert operations.free_tier_deducted == 13_000_000
        assert operations.quantity == 7_000_000
        assert operations.free_tier_applied is True

    def test_brokered_connections_tier_included_usage(self) -> None:
        model = get_azure_pricing_model("Azure Service Bus")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "messaging_tier": "Standard",
                "queue_operations": 1_000_000,
                "brokered_connections": 1500,
            },
        )
        raw = calculate_azure_sku_quantities(model, resolution.resolved)

        tier_included = [item for item in raw.included_usage if item.source == "tier"]
        assert len(tier_included) == 1
        assert tier_included[0].sku_key == "brokered_connections"
        assert tier_included[0].quantity == 1000

        connections = _quantity(raw, "brokered_connections")
        assert connections.raw_quantity == 1500
        assert connections.quantity == 500


class TestUnmappedSkuWarnings:
    def test_unmapped_sku_emits_warning(self) -> None:
        model = get_azure_pricing_model("Azure Container Apps")
        resolution = resolve_usage_assumptions(
            model,
            user_provided={
                "requests_per_month": 100_000,
                "avg_request_duration_seconds": 0.25,
                "cpu": 0.5,
                "memory_gb": 1.0,
                "network_egress_gb": 50,
                "min_replicas": 0,
            },
        )
        adjusted, _ = _apply(model, resolution.resolved)

        assert any(
            "network_egress_gb" in warning or "No free-tier allowance mapping" in warning
            for warning in adjusted.warnings
        )
