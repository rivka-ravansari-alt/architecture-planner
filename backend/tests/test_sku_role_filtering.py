"""Tests for strict SKU role filtering via pricing profiles."""

from __future__ import annotations

import pytest

from app.config.params import PRICING_MODEL_LINEAR_SKU, PRICING_MODEL_MONITORING
from app.data.pricing_profiles_seed import build_pricing_profile_doc
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.calculators.profile_driven import ProfileDrivenCalculator
from app.services.cost_calculation.factory import CostCalculatorFactory
from app.services.cost_calculation.models import CalculationContext, PricingCatalogRecord, PricingProfile, BillableSkuConfig
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_engine import PricingEngine
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository


def _context(usage: dict[str, float]) -> CalculationContext:
    return CalculationContext(
        provider="azure",
        expected_users="100",
        stage="mvp",
        usage=usage,
    )


def test_monitoring_ignores_unknown_catalog_skus():
    """Azure Monitor-style catalog with many SKUs should only price logs + metrics."""
    record = PricingCatalogRecord(
        id="azure-monitor",
        name="Azure Monitor",
        provider="azure",
        skus={
            "log": {"sku_id": "log-1", "description": "Log Analytics ingestion", "unit_price_usd": 2.30, "usage_unit": "GiBy"},
            "metrics": {"sku_id": "metric-1", "description": "Metrics", "unit_price_usd": 0.10, "usage_unit": "1K metrics"},
            "voice_core": {"sku_id": "voice", "description": "Voice Core", "unit_price_usd": 50000.0, "usage_unit": "unit"},
            "notification_hubs": {"sku_id": "nh", "description": "Notification Hubs", "unit_price_usd": 10000.0, "usage_unit": "unit"},
            "data_ingestion": {"sku_id": "di", "description": "Data Ingestion", "unit_price_usd": 8000.0, "usage_unit": "GB"},
        },
        formula=PRICING_MODEL_MONITORING,
    )
    profile = PricingProfileRepository(FakeFirestoreClient())._profile_from_doc(
        build_pricing_profile_doc("azure", "Azure Monitor"),
        provider="azure",
    )
    usage = {"log_gb": 1.0, "metric_samples": 10_000}
    result = ProfileDrivenCalculator(profile).calculate(record, _context(usage))

    assert result.monthly_cost == pytest.approx(1.0 * 2.30 + (10_000 / 1000) * 0.10)
    assert "voice_core" in result.ignored_sku_roles
    assert "notification_hubs" in result.ignored_sku_roles
    priced_roles = {line.sku_role for line in result.sku_lines if line.line_item_cost > 0}
    assert priced_roles == {"log", "metrics"}


def test_linear_sku_model_is_unsupported():
    record = PricingCatalogRecord(
        id="generic",
        name="Generic Service",
        provider="aws",
        skus={"usage": {"sku_id": "u1", "unit_price_usd": 9999.0, "usage_unit": "mo"}},
        formula=PRICING_MODEL_LINEAR_SKU,
    )
    profile = PricingProfile(
        id="aws-generic",
        provider="aws",
        service_name="Generic Service",
        pricing_model=PRICING_MODEL_LINEAR_SKU,
        billable_skus={"usage": BillableSkuConfig(usage_metric="monthly_requests", conversion="none")},
    )
    factory = CostCalculatorFactory()
    assert factory.for_profile(profile) is None

    result = PricingEngine(calculator_factory=factory).calculate(
        record,
        profile,
        provider="aws",
        expected_users="100",
        stage="mvp",
        usage_metrics={"monthly_requests": 3000},
    )
    assert result.unsupported is True
    assert result.monthly_cost == 0.0


def test_required_total_excludes_optional_in_provider_cost():
    from app.config.params import FIRESTORE_COLLECTION_GCP_CATALOG, FIRESTORE_COLLECTION_GCP_PRICING_PROFILES

    client = FakeFirestoreClient()
    client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document("cloud-run").set({
        "id": "cloud-run",
        "name": "Cloud Run",
        "enabled": True,
        "skus": {
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
            "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
        },
        "formula": "compute_request_based",
    })
    client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document("cloud-storage").set({
        "id": "cloud-storage",
        "name": "Cloud Storage",
        "enabled": True,
        "skus": {"storage": {"sku_id": "gcs", "unit_price_usd": 0.020, "usage_unit": "GiBy.mo"}},
        "formula": "storage_based",
    })
    for service_name in ("Cloud Run", "Cloud Storage"):
        profile_doc = build_pricing_profile_doc("gcp", service_name)
        client.collection(FIRESTORE_COLLECTION_GCP_PRICING_PROFILES).document(profile_doc["id"]).set(profile_doc)

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
        ),
        MappedComponent(
            key="object_storage",
            name="Storage",
            component_type="object_storage",
            reason="",
            category="core",
            optional=True,
            order=1,
            cloud={"aws": [], "gcp": ["Cloud Storage"], "azure": []},
            implementation_options={},
        ),
    ]
    results = calculator.calculate(components=components, expected_users="100", stage="mvp")
    gcp = next(r for r in results if r.provider == "gcp")
    assert gcp.monthly_low == gcp.required_low
    assert gcp.monthly_high == gcp.required_high
    assert gcp.optional_high >= gcp.optional_low
