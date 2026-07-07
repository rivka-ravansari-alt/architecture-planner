"""Smoke tests for extended Azure SKU quantity calculators."""

from __future__ import annotations

import pytest

from app.pricing import calculate_azure_sku_quantities, get_azure_pricing_model, resolve_usage_assumptions

_EXTENDED_SAMPLES: dict[str, dict] = {
    "API Management": {"requests_per_month": 500_000, "data_egress_gb": 5},
    "Application Gateway": {"hours_per_month": 730, "capacity_unit_hours": 100},
    "Content Delivery Network": {"requests_per_month": 2_000_000, "data_transfer_gb": 50},
    "Azure App Service": {"instance_hours_per_month": 730, "requests_per_month": 100_000},
    "Azure App Center": {"build_minutes_per_month": 120},
    "Azure Cosmos DB": {"request_units_per_month": 5_000_000, "storage_gb": 25},
    "Azure Redis Cache": {"hours_per_month": 730},
    "Azure Cognitive Search": {"storage_gb": 10, "search_units_hours": 730},
    "Azure Foundry Models": {"input_tokens_per_month": 1_000_000, "output_tokens_per_month": 500_000},
    "Notification Hubs": {"push_notifications_per_month": 100_000},
    "Azure Voice Core": {"voice_minutes_per_month": 50},
    "Application Insights": {"telemetry_gb_per_month": 2},
    "Azure Monitor": {"metrics_count": 5, "alert_rules_count": 2},
    "Log Analytics": {"log_ingestion_gb_per_month": 3},
    "Power BI": {"pro_seats": 2},
    "Azure Key Vault": {"secrets_count": 5, "operations_per_month": 20_000},
    "Azure App Configuration": {"configuration_stores": 1, "requests_per_month": 50_000},
}


@pytest.mark.parametrize("service_name", sorted(_EXTENDED_SAMPLES))
def test_extended_service_produces_quantities(service_name: str) -> None:
    model = get_azure_pricing_model(service_name)
    assert model is not None

    resolution = resolve_usage_assumptions(
        model,
        user_provided=_EXTENDED_SAMPLES[service_name],
    )
    assert resolution.ready_for_calculation is True

    result = calculate_azure_sku_quantities(model, resolution.resolved)
    assert result.ready is True
    assert result.quantities
    assert all(item.quantity >= 0 for item in result.quantities)
