"""Tests for AWS pricing coverage and explicit unsupported handling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.models import Project
from app.pricing.aws.coverage import (
    build_aws_pricing_coverage_report,
    collect_catalog_aws_services,
    inspect_aws_service_coverage,
    is_aws_service_fully_supported,
)
from app.pricing.aws.project_costing import AwsProjectCostingPipeline, build_unsupported_component_result
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.schemas.domain import MappedComponent
from tests.aws_catalog_test_fixture import AwsCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "aws_pricing_coverage_report.py"


class TestAwsPricingCoverage:
    def test_catalog_lists_all_seed_aws_services(self) -> None:
        services = collect_catalog_aws_services()
        names = {item.service_name for item in services}
        assert "Lambda" in names
        assert "DynamoDB" in names
        assert "CloudFront" in names
        assert len(services) >= 25

    def test_fully_supported_core_services(self) -> None:
        report = build_aws_pricing_coverage_report()
        assert len(report.fully_supported) == len(collect_catalog_aws_services())
        for name in report.fully_supported:
            assert is_aws_service_fully_supported(name), name

    def test_unsupported_services_are_explicit(self) -> None:
        unknown = inspect_aws_service_coverage("Nonexistent AWS Service")
        assert not unknown.fully_supported
        assert unknown.coverage_group == "C"

    def test_dynamodb_is_default_database_option(self) -> None:
        entry = next(item for item in collect_catalog_aws_services() if item.service_name == "DynamoDB")
        assert "database" in entry.component_types
        assert "database" in entry.is_default_for_types

    def test_coverage_report_groups(self) -> None:
        report = build_aws_pricing_coverage_report()
        catalog_count = len(collect_catalog_aws_services())
        assert len(report.fully_supported) == catalog_count
        assert len(report.unsupported) == 0
        assert len(report.by_group["E_deferred_complex"]) == 0
        assert len(report.by_group["C_missing_pricing_model"]) == 0

    def test_coverage_script_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "AWS PRICING COVERAGE REPORT" in result.stdout


class TestAwsUnsupportedComponents:
    @pytest.fixture
    def pipeline(self) -> AwsProjectCostingPipeline:
        calculator = AwsCatalogTestFixture().build_cost_calculator()
        return AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)

    def test_unsupported_component_has_explicit_status(self) -> None:
        component = MappedComponent(
            key="custom",
            name="Custom",
            component_type="service",
            reason="",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Unknown AWS SKU", "azure": "Functions", "gcp": "Cloud Run"},
        )
        result = build_unsupported_component_result(component, "Unknown AWS SKU")
        assert result.pricing_status == "unsupported"
        assert result.unsupported_reason
        assert result.missing_implementation

    def test_mixed_architecture_reports_supported_and_unsupported(
        self,
        pipeline: AwsProjectCostingPipeline,
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
                key="cdn",
                name="CDN",
                component_type="cdn",
                reason="",
                category="core",
                optional=False,
                order=1,
                cloud={"aws": "CloudFront", "azure": "CDN", "gcp": "CDN"},
            ),
        ]
        result = pipeline.calculate(project, components)
        assert result.supported_component_count == 2
        assert result.unsupported_component_count == 0
        assert len(result.components) == 2
        api = next(item for item in result.components if item.component_id == "api")
        cdn = next(item for item in result.components if item.component_id == "cdn")
        assert api.pricing_status == "supported"
        assert cdn.pricing_status == "supported"
        assert cdn.service == "CloudFront"

    def test_dynamodb_database_is_supported(
        self,
        pipeline: AwsProjectCostingPipeline,
    ) -> None:
        project = Project(name="Test", description="", stage="mvp", expected_users="100")
        components = [
            MappedComponent(
                key="database",
                name="Database",
                component_type="database",
                reason="",
                category="core",
                optional=False,
                order=0,
                cloud={"aws": "DynamoDB", "azure": "Cosmos DB", "gcp": "Firestore"},
            ),
        ]
        result = pipeline.calculate(project, components)
        assert result.supported_component_count == 1
        assert result.unsupported_component_count == 0
        db = result.components[0]
        assert db.pricing_status == "supported"
        assert db.service == "DynamoDB"
