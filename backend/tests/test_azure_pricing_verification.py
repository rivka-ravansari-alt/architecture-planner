"""Tests for the full Azure pricing verification report."""

from __future__ import annotations

import pytest

from app.models import Project
from app.pricing.azure.verification import (
    AzurePricingReportFormatter,
    AzurePricingVerificationRunner,
)
from app.schemas.domain import MappedComponent
from tests.azure_catalog_test_fixture import AzureCatalogTestFixture


@pytest.fixture
def verification_runner() -> AzurePricingVerificationRunner:
    return AzurePricingVerificationRunner(AzureCatalogTestFixture().build_cost_calculator())


@pytest.fixture
def sample_architecture() -> tuple[Project, list[MappedComponent], dict[str, bool]]:
    project = Project(
        name="Verify",
        description="",
        expected_users="1000",
        stage="mvp",
    )
    components = [
        MappedComponent(
            key="api",
            name="API",
            component_type="service",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": "Functions"},
        ),
        MappedComponent(
            key="files",
            name="Files",
            component_type="object_storage",
            reason="",
            category="core",
            optional=False,
            order=1,
            cloud={"aws": "S3", "gcp": "Cloud Storage", "azure": "Blob Storage"},
        ),
    ]
    feature_flags = {
        "file_upload": True,
        "background_processing": False,
        "ai": False,
    }
    return project, components, feature_flags


class TestAzurePricingVerificationRunner:
    def test_runs_all_pipeline_stages(
        self,
        verification_runner: AzurePricingVerificationRunner,
        sample_architecture,
    ) -> None:
        project, components, feature_flags = sample_architecture
        report = verification_runner.run(project, components, feature_flags=feature_flags)

        assert len(report.components) == 2
        assert report.total_usd >= 0

        for component in report.components:
            assert component.architecture.component_name
            assert component.azure_service
            assert component.usage_assumptions
            assert component.resolved_assumptions
            assert component.raw_sku_quantities
            assert component.billable_sku_quantities
            assert component.sku_lines

            for line in component.sku_lines:
                assert line.sku_key
                assert line.unit
                assert line.raw_quantity is not None or line.billable_quantity == 0

    def test_blob_free_tier_shows_deduction(
        self,
        verification_runner: AzurePricingVerificationRunner,
        sample_architecture,
    ) -> None:
        project, components, feature_flags = sample_architecture
        report = verification_runner.run(project, components, feature_flags=feature_flags)
        blob = next(item for item in report.components if item.architecture.component_id == "files")
        storage_line = next(item for item in blob.sku_lines if item.sku_key == "storage_gb_month")

        assert storage_line.raw_quantity is not None
        assert storage_line.raw_quantity > storage_line.billable_quantity
        assert storage_line.free_tier_deducted > 0
        assert storage_line.unit_price_usd is not None
        assert storage_line.sku_cost_usd is not None

    def test_user_scale_changes_totals(
        self,
        verification_runner: AzurePricingVerificationRunner,
    ) -> None:
        component = MappedComponent(
            key="api",
            name="API",
            component_type="service",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": "Functions"},
        )
        small = verification_runner.run(
            Project(name="Small", description="", expected_users="100", stage="mvp"),
            [component],
        )
        large = verification_runner.run(
            Project(name="Large", description="", expected_users="10000", stage="mvp"),
            [component],
        )
        assert large.total_usd > small.total_usd

    def test_formatter_includes_stage_headers(
        self,
        verification_runner: AzurePricingVerificationRunner,
        sample_architecture,
    ) -> None:
        project, components, feature_flags = sample_architecture
        report = verification_runner.run(project, components, feature_flags=feature_flags)
        text = AzurePricingReportFormatter().format(report)

        for header in (
            "[1] Architecture / component input",
            "[2] Usage assumptions",
            "[3] Resolved assumptions",
            "[4] Raw SKU quantities",
            "[5] Free tier / included usage deducted",
            "[6] Billable SKU quantities",
            "[7] Catalog price lookup",
            "[8] Final SKU cost",
            "Total monthly cost (USD)",
        ):
            assert header in text
