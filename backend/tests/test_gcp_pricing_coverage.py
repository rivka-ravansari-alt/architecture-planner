"""Tests for GCP pricing coverage and explicit unsupported handling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.models import Project
from app.pricing.gcp.coverage import (
    build_gcp_pricing_coverage_report,
    collect_catalog_gcp_services,
    inspect_gcp_service_coverage,
    is_gcp_service_fully_supported,
)
from app.pricing.gcp.project_costing import (
    GcpProjectCostingPipeline,
    build_ui_only_component_result,
    build_unsupported_component_result,
)
from app.pricing.gcp.ui_only import LOOKER_STUDIO_UI_ONLY_NOTE, is_gcp_ui_only_service
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.schemas.domain import MappedComponent
from tests.gcp_catalog_test_fixture import GcpCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "gcp_pricing_coverage_report.py"


class TestGcpPricingCoverage:
    def test_catalog_lists_core_gcp_services(self) -> None:
        services = collect_catalog_gcp_services()
        names = {item.service_name for item in services}
        assert "Cloud Run" in names
        assert "Cloud Storage" in names
        assert "Cloud SQL" in names
        assert len(services) >= 20

    def test_fully_supported_core_services(self) -> None:
        report = build_gcp_pricing_coverage_report()
        for name in ("Cloud Run", "Cloud Storage", "Cloud SQL", "Cloud Pub/Sub"):
            assert is_gcp_service_fully_supported(name), name
        assert "Cloud Run" in report.fully_supported

    def test_unsupported_services_are_explicit(self) -> None:
        unknown = inspect_gcp_service_coverage("Nonexistent GCP Service")
        assert not unknown.fully_supported
        assert unknown.coverage_group == "C"

    def test_cloud_firestore_is_default_database_option(self) -> None:
        entry = next(
            item for item in collect_catalog_gcp_services() if item.service_name == "Cloud Firestore"
        )
        assert "database" in entry.component_types
        assert "database" in entry.is_default_for_types

    def test_looker_studio_is_ui_only_not_unsupported(self) -> None:
        coverage = inspect_gcp_service_coverage("Looker Studio")
        assert coverage.coverage_group == "U"
        assert not coverage.fully_supported
        assert is_gcp_ui_only_service("Looker Studio")

        component = MappedComponent(
            key="analytics",
            name="Analytics",
            component_type="analytics",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "QuickSight", "azure": "Power BI", "gcp": "Looker Studio"},
        )
        result = build_ui_only_component_result(component, "Looker Studio")
        assert result.pricing_status == "ui_only"
        assert result.subtotal_usd == 0.0
        assert result.pricing_note == LOOKER_STUDIO_UI_ONLY_NOTE
        assert result.ready is True

    def test_coverage_report_groups(self) -> None:
        report = build_gcp_pricing_coverage_report()
        assert len(report.fully_supported) >= 20
        assert "Looker Studio" in report.ui_only
        assert len(report.by_group["U_ui_only"]) == 1
        assert len(report.by_group["C_missing_pricing_model"]) == 0
        assert len(report.by_group["E_deferred_complex"]) == 0

    def test_coverage_script_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "GCP PRICING COVERAGE REPORT" in result.stdout


class TestGcpUnsupportedComponents:
    @pytest.fixture
    def pipeline(self) -> GcpProjectCostingPipeline:
        calculator = GcpCatalogTestFixture().build_cost_calculator()
        return GcpProjectCostingPipeline(GcpUsageInferenceEngine(), calculator)

    def test_unsupported_component_has_explicit_status(self) -> None:
        component = MappedComponent(
            key="custom",
            name="Custom",
            component_type="service",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Unknown GCP SKU"},
        )
        result = build_unsupported_component_result(component, "Unknown GCP SKU")
        assert result.pricing_status == "unsupported"
        assert result.unsupported_reason
        assert result.missing_implementation

    def test_mixed_architecture_with_ui_only_and_unsupported(
        self,
        pipeline: GcpProjectCostingPipeline,
    ) -> None:
        project = Project(name="Test", description="", stage="mvp", expected_users="100")
        components = [
            MappedComponent(
                key="api",
                name="API",
                component_type="service",
                reason="",
                category="core",
                optional=False,
                order=0,
                cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Cloud Run"},
            ),
            MappedComponent(
                key="analytics",
                name="Analytics",
                component_type="analytics",
                reason="",
                category="core",
                optional=False,
                order=1,
                cloud={"aws": "QuickSight", "azure": "Power BI", "gcp": "Looker Studio"},
            ),
            MappedComponent(
                key="custom",
                name="Custom",
                component_type="service",
                reason="",
                category="core",
                optional=False,
                order=2,
                cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Unknown GCP SKU"},
            ),
        ]
        result = pipeline.calculate(project, components)
        assert result.supported_component_count == 1
        assert result.ui_only_component_count == 1
        assert result.unsupported_component_count == 1
        assert len(result.components) == 3
        api = next(item for item in result.components if item.component_id == "api")
        analytics = next(item for item in result.components if item.component_id == "analytics")
        custom = next(item for item in result.components if item.component_id == "custom")
        assert api.pricing_status == "supported"
        assert analytics.pricing_status == "ui_only"
        assert analytics.subtotal_usd == 0.0
        assert analytics.pricing_note == LOOKER_STUDIO_UI_ONLY_NOTE
        assert custom.pricing_status == "unsupported"

    def test_mixed_architecture_reports_supported_and_unsupported(
        self,
        pipeline: GcpProjectCostingPipeline,
    ) -> None:
        project = Project(name="Test", description="", stage="mvp", expected_users="100")
        components = [
            MappedComponent(
                key="api",
                name="API",
                component_type="service",
                reason="",
                category="core",
                optional=False,
                order=0,
                cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Cloud Run"},
            ),
            MappedComponent(
                key="custom",
                name="Custom",
                component_type="service",
                reason="",
                category="core",
                optional=False,
                order=1,
                cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Unknown GCP SKU"},
            ),
        ]
        result = pipeline.calculate(project, components)
        assert result.supported_component_count == 1
        assert result.unsupported_component_count == 1
        assert len(result.components) == 2
        api = next(item for item in result.components if item.component_id == "api")
        custom = next(item for item in result.components if item.component_id == "custom")
        assert api.pricing_status == "supported"
        assert custom.pricing_status == "unsupported"

    def test_cloud_storage_object_storage_is_supported(
        self,
        pipeline: GcpProjectCostingPipeline,
    ) -> None:
        project = Project(name="Test", description="", stage="mvp", expected_users="100")
        components = [
            MappedComponent(
                key="storage",
                name="Storage",
                component_type="object_storage",
                reason="",
                category="core",
                optional=False,
                order=0,
                cloud={"aws": "S3", "azure": "Blob Storage", "gcp": "Cloud Storage"},
            ),
        ]
        result = pipeline.calculate(project, components)
        assert result.supported_component_count == 1
        assert result.unsupported_component_count == 0
        storage = result.components[0]
        assert storage.pricing_status == "supported"
        assert storage.service == "Cloud Storage"
