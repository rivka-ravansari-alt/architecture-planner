"""Tests for pricing-profile-driven cost calculation."""

from __future__ import annotations

import pytest

from app.config.params import (
    FIRESTORE_COLLECTION_GCP_CATALOG,
    PRICING_MODEL_COMPUTE_REQUEST,
)
from app.data.pricing_profiles_seed import build_pricing_profile_doc
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.models import CalculationContext, PricingCatalogRecord
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_engine import PricingEngine
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.services.cost_calculation.unit_conversions import apply_conversion
from tests.cost_fixtures import seed_test_pricing_catalog


def _profile(provider: str, service_name: str):
    repo = PricingProfileRepository(FakeFirestoreClient())
    return repo._profile_from_doc(
        build_pricing_profile_doc(provider, service_name),
        provider=provider,
    )


def _cloud_run_catalog() -> PricingCatalogRecord:
    return PricingCatalogRecord(
        id="cloud-run",
        name="Cloud Run",
        provider="gcp",
        skus={
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
            "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
            "network": {"sku_id": "cr-net", "unit_price_usd": 99.0, "usage_unit": "GiBy"},
        },
        formula="compute_request_based",
    )


def test_unit_conversions_are_safe_and_predefined():
    quantity, note = apply_conversion(3_600.0, "seconds_to_hours")
    assert quantity == pytest.approx(1.0)
    assert "3600" in note

    quantity, _ = apply_conversion(2_000_000.0, "per_million")
    assert quantity == pytest.approx(2.0)

    with pytest.raises(Exception):
        apply_conversion(1.0, "eval(1+1)")


def test_normal_calculation_uses_profile_billable_skus_only():
    usage = {
        "cpu_seconds": 7200.0,
        "memory_gib_seconds": 3600.0,
        "monthly_requests": 2_000_000.0,
    }
    result = PricingEngine().calculate(
        _cloud_run_catalog(),
        _profile("gcp", "Cloud Run"),
        provider="gcp",
        expected_users="100",
        stage="mvp",
        usage_metrics=usage,
    )

    assert result.pricing_model == PRICING_MODEL_COMPUTE_REQUEST
    assert result.pricing_profile_service == "Cloud Run"
    assert set(result.billable_sku_roles) == {"cpu", "memory", "requests"}
    assert "network" not in {line.sku_role for line in result.sku_lines}
    roles = {line.sku_role: line for line in result.sku_lines}
    assert roles["cpu"].conversion == "seconds_to_hours"
    assert roles["requests"].calculated_quantity == pytest.approx(2.0)
    assert result.monthly_cost > 0


def test_missing_catalog_sku_is_not_guessed():
    record = PricingCatalogRecord(
        id="cloud-run",
        name="Cloud Run",
        provider="gcp",
        skus={
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
        },
        formula="compute_request_based",
    )
    result = PricingEngine().calculate(
        record,
        _profile("gcp", "Cloud Run"),
        provider="gcp",
        expected_users="100",
        stage="mvp",
        usage_metrics={"cpu_seconds": 100.0, "memory_gib_seconds": 100.0, "monthly_requests": 1000.0},
    )

    assert result.missing_catalog_skus is True
    assert any("Required billable SKU role 'requests'" in warning for warning in result.warnings)


def test_missing_profile_reports_unknown_item():
    client = FakeFirestoreClient()
    client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document("cloud-run").set({
        "id": "cloud-run",
        "name": "Cloud Run",
        "enabled": True,
        "skus": {
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025},
            "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40},
        },
        "formula": "compute_request_based",
    })

    calculator = ArchitectureCostCalculator(
        PricingCatalogRepository(client),
        pricing_profiles=PricingProfileRepository(client),
    )
    components = [
        MappedComponent(
            key="service",
            name="API",
            component_type="api",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": [], "gcp": ["Cloud Run"], "azure": []},
            implementation_options={},
        )
    ]
    gcp = next(r for r in calculator.calculate(components=components, expected_users="100", stage="mvp") if r.provider == "gcp")
    assert gcp.required_low == 0.0
    assert any("no pricing profile" in item for item in gcp.unknown_items)


def test_seeded_profiles_enable_end_to_end_pricing():
    client = FakeFirestoreClient()
    seed_test_pricing_catalog(client)
    calculator = ArchitectureCostCalculator(
        PricingCatalogRepository(client),
        pricing_profiles=PricingProfileRepository(client),
    )
    components = [
        MappedComponent(
            key="service",
            name="API",
            component_type="api",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": [], "gcp": ["Cloud Run"], "azure": []},
            implementation_options={},
        )
    ]
    gcp = next(r for r in calculator.calculate(components=components, expected_users="100", stage="mvp") if r.provider == "gcp")
    assert gcp.component_breakdown[0]["final_component_cost"] > 0
    breakdown = gcp.pricing_debug_table[0]
    assert breakdown["pricing_profile_service"] == "Cloud Run"
    assert "cpu" in breakdown["billable_sku_roles"]
