"""Tests for Azure pricing model definitions and assumption resolution."""

from __future__ import annotations

import pytest

from app.pricing import (
    AZURE_PRICING_MODELS,
    AssumptionConfidence,
    AssumptionSource,
    UsageAssumption,
    get_azure_pricing_model,
    list_azure_pricing_models_for_component_type,
    resolve_usage_assumptions,
)

EXPECTED_SERVICES = {
    "Azure Container Apps",
    "Azure SQL Database",
    "Azure Blob Storage",
    "Azure Queue Storage",
    "Azure Service Bus",
    "Azure Functions",
}


@pytest.mark.parametrize("service_name", sorted(EXPECTED_SERVICES))
def test_azure_pricing_model_registered(service_name: str) -> None:
    model = get_azure_pricing_model(service_name)
    assert model is not None
    assert model.cloud == "azure"
    assert model.service == service_name


def test_all_models_have_required_metadata() -> None:
    assert len(AZURE_PRICING_MODELS) == len(EXPECTED_SERVICES)

    for model in AZURE_PRICING_MODELS:
        details = model.pricing_model
        assert model.component_types
        assert details.required_inputs
        assert details.calculated_skus
        assert details.billing_unit
        assert details.billing_granularity

        input_keys = {item.key for item in details.required_inputs}
        for sku in details.calculated_skus:
            assert sku.input_keys, f"{model.service}:{sku.key} must declare input_keys"
            assert sku.catalog_sku_roles, f"{model.service}:{sku.key} must map catalog roles"
            assert all(key in input_keys for key in sku.input_keys), (
                f"{model.service}:{sku.key} references unknown inputs"
            )


def test_catalog_service_name_lookup() -> None:
    assert get_azure_pricing_model("Blob Storage") is not None
    assert get_azure_pricing_model("Functions") is not None
    assert get_azure_pricing_model("SQL Database") is not None

    queue_models = list_azure_pricing_models_for_component_type("queue")
    queue_names = {model.service for model in queue_models}
    assert queue_names == {"Azure Queue Storage", "Azure Service Bus"}

    service_models = list_azure_pricing_models_for_component_type("service")
    service_names = {model.service for model in service_models}
    assert "Azure Container Apps" in service_names
    assert "Azure Functions" in service_names


def test_missing_assumptions_are_reported_not_invented() -> None:
    model = get_azure_pricing_model("Azure Blob Storage")
    assert model is not None

    result = resolve_usage_assumptions(model, user_provided={}, inferred={})

    assert result.ready_for_calculation is False
    assert any(item.key == "storage_gb" for item in result.missing)
    assert all(item.key != "access_tier" for item in result.missing)


def test_defaults_fill_optional_inputs_with_source_and_confidence() -> None:
    model = get_azure_pricing_model("Azure Blob Storage")
    assert model is not None

    result = resolve_usage_assumptions(
        model,
        user_provided={"storage_gb": 120},
        inferred={},
    )

    assert result.ready_for_calculation is True
    storage = next(item for item in result.resolved if item.key == "storage_gb")
    assert storage.source == AssumptionSource.user_provided
    assert storage.confidence == AssumptionConfidence.high

    access_tier = next(item for item in result.resolved if item.key == "access_tier")
    assert access_tier.source == AssumptionSource.default
    assert access_tier.confidence == AssumptionConfidence.medium


def test_inferred_assumptions_preserve_confidence_and_reasoning() -> None:
    model = get_azure_pricing_model("Azure Functions")
    assert model is not None

    inferred = {
        "executions_per_month": UsageAssumption(
            key="executions_per_month",
            value=2_500_000,
            unit="executions/month",
            source=AssumptionSource.inferred,
            confidence=AssumptionConfidence.low,
            reasoning="High-traffic social app with frequent polling.",
        )
    }
    result = resolve_usage_assumptions(model, user_provided={}, inferred=inferred)

    execution = next(item for item in result.resolved if item.key == "executions_per_month")
    assert execution.source == AssumptionSource.inferred
    assert execution.confidence == AssumptionConfidence.low
    assert execution.reasoning == "High-traffic social app with frequent polling."
    assert result.ready_for_calculation is True


def test_container_apps_free_tier_defined() -> None:
    model = get_azure_pricing_model("Azure Container Apps")
    assert model is not None
    assert model.pricing_model.free_tier is not None
    assert model.pricing_model.free_tier.allowances["requests"] == 2_000_000
