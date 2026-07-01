"""Deterministic baseline cost scenario: 100-user CRUD SaaS without AI/uploads/notifications."""

from __future__ import annotations

import pytest

from app.config.params import CLOUD_PROVIDERS, COST_SANITY_COMPONENT_MAX_100_USERS, COST_SANITY_REQUIRED_MAX_100_USERS
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from tests.cost_fixtures import seed_test_pricing_catalog


def _baseline_usage_profile() -> dict[str, object]:
    return {
        "monthly_active_users": "100",
        "user_activity": "moderate",
        "file_uploads_enabled": False,
        "ai_enabled": False,
        "notification_channels": [],
        "background_jobs": "none",
    }


def _crud_saas_components() -> list[MappedComponent]:
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
            key="service",
            name="Application Service",
            component_type="service",
            reason="Business logic",
            category="core",
            optional=False,
            order=1,
            cloud={
                "aws": ["Lambda"],
                "gcp": ["Cloud Run"],
                "azure": ["Functions"],
            },
            implementation_options={"recommended": "managed_service"},
        ),
        MappedComponent(
            key="database",
            name="Database",
            component_type="database",
            reason="Persistent data",
            category="core",
            optional=False,
            order=2,
            cloud={
                "aws": ["DynamoDB"],
                "gcp": ["Cloud Firestore"],
                "azure": ["Azure Cosmos DB"],
            },
            implementation_options={"recommended": "managed_service"},
        ),
        MappedComponent(
            key="api_gateway",
            name="API Gateway",
            component_type="api_gateway",
            reason="API routing",
            category="core",
            optional=False,
            order=3,
            cloud={
                "aws": ["API Gateway"],
                "gcp": ["API Gateway"],
                "azure": ["API Management"],
            },
            implementation_options={"recommended": "managed_service"},
        ),
    ]


@pytest.fixture
def baseline_calculator() -> ArchitectureCostCalculator:
    client = FakeFirestoreClient()
    seed_test_pricing_catalog(client)
    return ArchitectureCostCalculator(
        PricingCatalogRepository(client),
        pricing_profiles=PricingProfileRepository(client),
    )


def test_baseline_100_user_crud_saas_reasonable_totals(baseline_calculator):
    results = baseline_calculator.calculate(
        components=_crud_saas_components(),
        expected_users="100",
        stage="mvp",
        usage_profile=_baseline_usage_profile(),
    )
    assert len(results) == len(CLOUD_PROVIDERS)

    for estimate in results:
        assert estimate.required_high <= COST_SANITY_REQUIRED_MAX_100_USERS, (
            f"{estimate.provider} required high ${estimate.required_high} exceeds "
            f"${COST_SANITY_REQUIRED_MAX_100_USERS}"
        )
        assert estimate.required_high < 10_000, (
            f"{estimate.provider} returned tens of thousands: ${estimate.required_high}"
        )

        for row in estimate.pricing_debug_table:
            cost = row.get("component_monthly_cost") or row.get("final_component_cost") or 0.0
            if row.get("included_in_total"):
                assert cost <= COST_SANITY_COMPONENT_MAX_100_USERS, (
                    f"{estimate.provider}/{row.get('component_name')}: ${cost} exceeds component cap"
                )
            assert row.get("sku_lines"), (
                f"{estimate.provider}/{row.get('component_name')}: missing SKU audit in debug table"
            )


def test_baseline_gcp_serverless_under_50_usd(baseline_calculator):
    gcp = next(
        item
        for item in baseline_calculator.calculate(
            components=_crud_saas_components(),
            expected_users="100",
            stage="mvp",
            usage_profile=_baseline_usage_profile(),
        )
        if item.provider == "gcp"
    )
    assert gcp.required_high <= 50.0, f"GCP required high ${gcp.required_high} expected <= $50"
    assert gcp.required_low >= 0.0
    assert len(gcp.pricing_debug_table) == 4
