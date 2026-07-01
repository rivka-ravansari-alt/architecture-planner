"""Tests for suspicious cost exclusion and required-only totals."""

from __future__ import annotations

import pytest

from app.config.params import FIRESTORE_COLLECTION_AWS_CATALOG, FIRESTORE_COLLECTION_AWS_PRICING_PROFILES
from app.data.pricing_profiles_seed import build_pricing_profile_doc
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.models import CostCalculationResult, PricingProfile, BillableSkuConfig
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_engine import PricingEngine
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.services.cost_calculation.suspicious_cost_guard import should_exclude_required_component


class _ExpensiveEngine(PricingEngine):
    def calculate(self, record, profile, *, provider, expected_users, stage, usage_metrics):
        return CostCalculationResult(
            monthly_cost=50_000.0,
            pricing_model=profile.pricing_model,
            usage_assumptions=dict(usage_metrics),
            warnings=[],
            pricing_profile_id=profile.id,
            pricing_profile_service=profile.service_name,
            billable_sku_roles=sorted(profile.billable_skus.keys()),
        )


def test_should_exclude_required_component_over_200_for_100_users():
    assert should_exclude_required_component(250.0, optional=False, expected_users="100") is True
    assert should_exclude_required_component(150.0, optional=False, expected_users="100") is False
    assert should_exclude_required_component(50_000.0, optional=True, expected_users="100") is False


def test_should_exclude_required_component_over_1000_for_1000_users():
    assert should_exclude_required_component(1_500.0, optional=False, expected_users="1000") is True
    assert should_exclude_required_component(800.0, optional=False, expected_users="1000") is False
    assert should_exclude_required_component(50_000.0, optional=False, expected_users="10000") is False


def test_suspicious_required_component_excluded_from_total():
    client = FakeFirestoreClient()
    client.collection(FIRESTORE_COLLECTION_AWS_CATALOG).document("api-gateway").set({
        "id": "api-gateway",
        "name": "API Gateway",
        "enabled": True,
        "skus": {
            "cpu": {"sku_id": "cpu", "unit_price_usd": 0.000024},
            "memory": {"sku_id": "mem", "unit_price_usd": 0.0000025},
            "requests": {"sku_id": "req", "unit_price_usd": 0.40},
        },
        "formula": "compute_request_based",
    })
    profile_doc = build_pricing_profile_doc("aws", "API Gateway")
    client.collection(FIRESTORE_COLLECTION_AWS_PRICING_PROFILES).document(profile_doc["id"]).set(profile_doc)

    calculator = ArchitectureCostCalculator(
        PricingCatalogRepository(client),
        pricing_profiles=PricingProfileRepository(client),
        pricing_engine=_ExpensiveEngine(),
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
            cloud={"aws": ["API Gateway"], "gcp": [], "azure": []},
            implementation_options={},
        )
    ]

    aws = calculator.calculate(components=components, expected_users="100", stage="mvp")[0]
    assert aws.required_low == 0.0
    assert aws.required_high == 0.0
    assert aws.monthly_low == aws.required_low
    assert aws.monthly_high == aws.required_high
    assert any("suspicious_component_cost" in item for item in aws.unknown_items)
    assert len(aws.pricing_debug_table) == 1
    assert aws.pricing_debug_table[0]["included_in_total"] is False
    assert aws.pricing_debug_table[0]["exclusion_reason"] == "suspicious_component_cost"


def test_monthly_total_never_includes_optional():
    client = FakeFirestoreClient()
    client.collection(FIRESTORE_COLLECTION_AWS_CATALOG).document("lambda").set({
        "id": "lambda",
        "name": "Lambda",
        "enabled": True,
        "skus": {
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
            "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
        },
        "formula": "compute_request_based",
    })
    client.collection(FIRESTORE_COLLECTION_AWS_CATALOG).document("s3").set({
        "id": "s3",
        "name": "S3",
        "enabled": True,
        "skus": {"storage": {"sku_id": "s3-storage", "unit_price_usd": 0.023, "usage_unit": "GiBy.mo"}},
        "formula": "storage_based",
    })
    for service_name in ("Lambda", "S3"):
        profile_doc = build_pricing_profile_doc("aws", service_name)
        client.collection(FIRESTORE_COLLECTION_AWS_PRICING_PROFILES).document(profile_doc["id"]).set(profile_doc)

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
            cloud={"aws": ["Lambda"], "gcp": [], "azure": []},
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
            cloud={"aws": ["S3"], "gcp": [], "azure": []},
            implementation_options={},
        ),
    ]
    aws = next(
        item
        for item in calculator.calculate(components=components, expected_users="100", stage="mvp")
        if item.provider == "aws"
    )
    assert aws.monthly_low == aws.required_low
    assert aws.monthly_high == aws.required_high
    assert aws.optional_high >= aws.optional_low
