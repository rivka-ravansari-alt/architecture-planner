"""Tests for AWS multi-scenario pricing benchmark."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.pricing.aws.benchmark import (
    AWS_BENCHMARK_SCENARIOS,
    AwsScenarioPricingBenchmark,
    AwsScenarioPricingBenchmarkFormatter,
    build_usage_service,
    normalize_aws_components,
)
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS
from app.pricing.azure.scenarios import scenario_components
from tests.aws_catalog_test_fixture import AwsCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "benchmark_aws_scenarios.py"


@pytest.fixture
def heuristic_benchmark_report():
    calculator = AwsCatalogTestFixture().build_cost_calculator()
    pipeline = AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)
    usage_service = build_usage_service(inference_mode="heuristic")
    return AwsScenarioPricingBenchmark(
        pipeline,
        usage_service,
        inference_mode="heuristic",
    ).run()


class TestAwsScenarioPricingBenchmark:
    def test_runs_five_scenarios_and_user_counts(self, heuristic_benchmark_report) -> None:
        assert len(heuristic_benchmark_report.scenarios) == 5
        assert [s.scenario_id for s in heuristic_benchmark_report.scenarios] == [
            scenario.scenario_id for scenario in AWS_BENCHMARK_SCENARIOS
        ]
        expected_runs = len(AWS_BENCHMARK_SCENARIOS) * len(BENCHMARK_USER_COUNTS)
        actual_runs = sum(len(s.rows) for s in heuristic_benchmark_report.scenarios)
        assert actual_runs == expected_runs

    def test_each_scenario_has_architecture_components(self, heuristic_benchmark_report) -> None:
        for scenario in heuristic_benchmark_report.scenarios:
            assert scenario.architecture_components
            assert len(scenario.architecture_components) >= 3

    def test_totals_increase_monotonically_per_scenario(self, heuristic_benchmark_report) -> None:
        for scenario in heuristic_benchmark_report.scenarios:
            totals = [row.total_usd for row in scenario.rows]
            assert totals == sorted(totals)
            assert totals[-1] >= totals[0]

    def test_each_run_has_component_cost_lines(self, heuristic_benchmark_report) -> None:
        for scenario in heuristic_benchmark_report.scenarios:
            for row in scenario.rows:
                assert len(row.components) == len(scenario.architecture_components)
                for comp in row.components:
                    assert comp.aws_service
                    assert comp.behavioral_assumptions or comp.resolved_assumptions

    def test_normalize_aws_components_maps_rds_alias(self) -> None:
        components = normalize_aws_components(scenario_components(AWS_BENCHMARK_SCENARIOS[0]))
        rds = next(c for c in components if c.key == "database")
        assert rds.cloud["aws"] == "RDS"

    def test_formatter_produces_summary_table(self, heuristic_benchmark_report) -> None:
        text = AwsScenarioPricingBenchmarkFormatter.format_summary_table(heuristic_benchmark_report)
        assert "AWS SCENARIO PRICING BENCHMARK" in text
        for scenario in heuristic_benchmark_report.scenarios:
            assert scenario.name[:20] in text or scenario.name in text

    def test_benchmark_script_runs_heuristic_mode(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--mode", "heuristic", "--json"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert len(payload["scenarios"]) == 5


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestAwsScenarioPricingBenchmarkLLM:
    def test_llm_inference_runs_for_self_esteem(self) -> None:
        from app.clients.ai_client import AIClientFactory

        calculator = AwsCatalogTestFixture().build_cost_calculator()
        pipeline = AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)
        usage_service = build_usage_service(ai_client=AIClientFactory.create(), inference_mode="llm")
        report = AwsScenarioPricingBenchmark(
            pipeline,
            usage_service,
            inference_mode="llm",
            scenarios=(AWS_BENCHMARK_SCENARIOS[1],),  # self_esteem only — faster
        ).run()
        assert report.scenarios[0].rows[0].inference_source in {"llm", "llm_with_heuristic_fallback"}
