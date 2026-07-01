"""Tests for Firestore-backed architecture cost calculation."""

from __future__ import annotations

import pytest

from app.config.params import CLOUD_PROVIDERS
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.formula_classifier import resolve_pricing_model
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.services.cost_estimator_service import CostEstimatorService
from tests.cost_fixtures import seed_test_pricing_catalog


@pytest.fixture
def pricing_firestore() -> FakeFirestoreClient:
    client = FakeFirestoreClient()
    seed_test_pricing_catalog(client)
    return client


@pytest.fixture
def cost_calculator(pricing_firestore) -> ArchitectureCostCalculator:
    return ArchitectureCostCalculator(
        PricingCatalogRepository(pricing_firestore),
        pricing_profiles=PricingProfileRepository(pricing_firestore),
    )


def _sample_components() -> list[MappedComponent]:
    return [
        MappedComponent(
            key="web_app",
            name="Web Client",
            component_type="web_app",
            reason="Browser UI",
            category="core",
            optional=False,
            order=0,
            cloud={
                "aws": ["Amplify Hosting"],
                "gcp": ["Firebase Hosting"],
                "azure": ["Azure App Service"],
            },
            implementation_options={"recommended": "managed_service"},
        ),
        MappedComponent(
            key="object_storage",
            name="Object Storage",
            component_type="object_storage",
            reason="File uploads",
            category="core",
            optional=True,
            order=100,
            cloud={"aws": ["S3"], "gcp": ["Cloud Storage"], "azure": ["Blob Storage"]},
            implementation_options={"recommended": "managed_service"},
        ),
    ]


def test_resolve_pricing_model_detects_compute_request():
    formula = {
        "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
        "total": "cpu_cost",
    }
    assert resolve_pricing_model(formula) == "compute_request_based"


def test_resolve_pricing_model_accepts_string_key():
    assert resolve_pricing_model("storage_based") == "storage_based"


def test_catalog_repository_finds_by_service_name(pricing_firestore):
    repo = PricingCatalogRepository(pricing_firestore)
    record = repo.get_by_service_name("gcp", "Cloud Storage")
    assert record is not None
    assert record.name == "Cloud Storage"
    assert "storage" in record.skus


def test_calculator_sums_component_costs_per_provider(cost_calculator):
    results = cost_calculator.calculate(
        components=_sample_components(),
        expected_users="1000",
        stage="mvp",
    )
    assert len(results) == len(CLOUD_PROVIDERS)
    for estimate in results:
        assert estimate.monthly_low >= 0
        assert estimate.monthly_high >= estimate.monthly_low
        assert estimate.required_low > 0
        assert estimate.optional_high >= estimate.optional_low


def test_missing_pricing_is_reported_not_fatal(pricing_firestore):
    calculator = ArchitectureCostCalculator(
        PricingCatalogRepository(pricing_firestore),
        pricing_profiles=PricingProfileRepository(pricing_firestore),
    )
    components = [
        MappedComponent(
            key="api",
            name="Mystery API",
            component_type="api",
            reason="Unknown stack",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": ["Nonexistent Service"], "gcp": [], "azure": []},
            implementation_options={},
        )
    ]
    results = calculator.calculate(components=components, expected_users="100", stage="mvp")
    aws = next(item for item in results if item.provider == "aws")
    assert aws.monthly_low == 0
    assert aws.unknown_items


def test_cost_estimator_service_uses_injected_firestore(pricing_firestore):
    service = CostEstimatorService(firestore_client=pricing_firestore)
    costs = service.estimate_from_components(
        components=_sample_components(),
        expected_users="100",
        stage="mvp",
    )
    assert len(costs) == 3
