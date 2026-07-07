"""Tests for AWS platform scenario benchmark (extended services, random MAU)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.pricing.aws.benchmark import build_usage_service
from app.pricing.aws.platform_benchmark import (
    AwsPlatformScenarioBenchmark,
    AwsPlatformScenarioBenchmarkFormatter,
    assign_random_user_counts,
    user_count_to_project_label,
)
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.scenarios import AWS_EXTENDED_SERVICES, AWS_PLATFORM_BENCHMARK_SCENARIOS
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from tests.aws_catalog_test_fixture import AwsCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "benchmark_aws_platform_scenarios.py"


@pytest.fixture
def platform_report():
    calculator = AwsCatalogTestFixture().build_cost_calculator()
    pipeline = AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)
    usage_service = build_usage_service(inference_mode="heuristic")
    return AwsPlatformScenarioBenchmark(
        pipeline,
        usage_service,
        inference_mode="heuristic",
        random_seed=42,
    ).run()


class TestAwsPlatformScenarioBenchmark:
    def test_five_scenarios_with_random_user_assignments(self, platform_report) -> None:
        assert len(platform_report.scenarios) == 5
        assert len(platform_report.user_assignments) == 5
        assert platform_report.user_assignments == assign_random_user_counts(5, seed=42)
        for scenario in platform_report.scenarios:
            assert scenario.assigned_users == scenario.row.assigned_users
            assert scenario.assigned_users > 0

    def test_scenario_ids_match_definitions(self, platform_report) -> None:
        assert [s.scenario_id for s in platform_report.scenarios] == [
            scenario.scenario_id for scenario in AWS_PLATFORM_BENCHMARK_SCENARIOS
        ]

    def test_all_components_supported_with_catalog_costs(self, platform_report) -> None:
        for scenario in platform_report.scenarios:
            row = scenario.row
            assert row.unsupported_component_count == 0, scenario.scenario_id
            assert len(row.components) == len(scenario.architecture_components)
            for comp in row.components:
                status = row.pricing_status_by_component[comp.component_id]
                assert status in {"supported", "partial"}, (
                    f"{scenario.scenario_id}/{comp.component_id} -> {status}"
                )
                assert comp.aws_service
                assert comp.behavioral_assumptions or comp.resolved_assumptions
            assert row.supported_component_count + sum(
                1 for s in row.pricing_status_by_component.values() if s == "partial"
            ) == len(scenario.architecture_components)

    def test_extended_services_present_across_scenarios(self, platform_report) -> None:
        services_used: set[str] = set()
        for scenario in platform_report.scenarios:
            scenario_services = set(scenario.row.component_services)
            services_used.update(scenario_services)
            assert scenario_services & AWS_EXTENDED_SERVICES, scenario.scenario_id

        assert AWS_EXTENDED_SERVICES.issubset(services_used), services_used

    def test_totals_are_non_negative(self, platform_report) -> None:
        for scenario in platform_report.scenarios:
            assert scenario.row.total_usd >= 0.0
            for comp in scenario.row.components:
                assert comp.subtotal_usd >= 0.0

    def test_user_count_label_mapping(self) -> None:
        assert user_count_to_project_label(150) == "1000"
        assert user_count_to_project_label(850) == "1000"
        assert user_count_to_project_label(12_500) == "100000+"

    def test_formatter_produces_breakdown(self, platform_report) -> None:
        text = AwsPlatformScenarioBenchmarkFormatter.format_full_report(platform_report)
        assert "AWS PLATFORM SCENARIO BENCHMARK" in text
        assert "Mobile Wellness App" in text
        assert "AI Analytics Suite" in text
        assert "[supported]" in text or "[partial]" in text

    def test_service_price_table_headers(self, platform_report) -> None:
        table = AwsPlatformScenarioBenchmarkFormatter.format_service_price_table(platform_report)
        assert "App Name" in table
        assert "Users" in table
        assert "Service" in table
        assert "Price (USD)" in table
        assert "Mobile Wellness App" in table
        assert "TOTAL" in table
        assert "Bedrock" in table

    def test_platform_benchmark_script_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--mode", "heuristic", "--json", "--seed", "42"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert len(payload["scenarios"]) == 5
        assert payload["random_seed"] == 42
        for scenario in payload["scenarios"]:
            assert scenario["row"]["unsupported_component_count"] == 0
            assert scenario["row"]["total_usd"] >= 0
