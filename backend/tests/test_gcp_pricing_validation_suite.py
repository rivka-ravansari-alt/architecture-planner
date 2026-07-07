"""Tests for the GCP pricing validation suite."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS
from app.pricing.azure.scenarios import ALL_BENCHMARK_SCENARIOS, SELF_ESTEEM_HABIT, SIMPLE_CRUD_SAAS
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.pricing.gcp.validation_suite import (
    GcpPricingValidationSuite,
    GcpPricingValidationSuiteFormatter,
    ValidationStatus,
)
from tests.gcp_catalog_test_fixture import GcpCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "run_gcp_pricing_validation.py"


@pytest.fixture
def validation_report():
    calculator = GcpCatalogTestFixture().build_cost_calculator()
    pipeline = GcpProjectCostingPipeline(GcpUsageInferenceEngine(), calculator)
    return GcpPricingValidationSuite(pipeline).run()


class TestGcpPricingValidationSuite:
    def test_runs_all_scenarios_and_user_counts(self, validation_report) -> None:
        expected_runs = len(ALL_BENCHMARK_SCENARIOS) * len(BENCHMARK_USER_COUNTS)
        assert len(validation_report.scenario_runs) == expected_runs

    def test_self_esteem_costs_increase_monotonically(self, validation_report) -> None:
        runs = [
            run
            for run in validation_report.scenario_runs
            if run.scenario_id == SELF_ESTEEM_HABIT.scenario_id
        ]
        totals = [run.total_monthly_cost_usd for run in runs]
        assert totals == sorted(totals)
        assert totals[-1] > totals[0]

    def test_each_run_has_validation_checks(self, validation_report) -> None:
        for run in validation_report.scenario_runs:
            rule_ids = {check.rule_id for check in run.validation_checks}
            assert "non_negative_total" in rule_ids
            assert "catalog_completeness" in rule_ids

    def test_no_failed_validation_checks(self, validation_report) -> None:
        failures = [
            check
            for run in validation_report.scenario_runs
            for check in run.validation_checks
            if check.status == ValidationStatus.FAIL
        ]
        assert failures == []

    def test_expected_cost_ranges_defined_for_core_scenarios(self, validation_report) -> None:
        core_runs = [
            run
            for run in validation_report.scenario_runs
            if run.scenario_id in {"simple_crud_saas", "self_esteem_habit", "ecommerce"}
        ]
        assert core_runs
        for run in core_runs:
            assert run.expected_cost_range is not None

    def test_simple_crud_below_ecommerce_at_100_users(self, validation_report) -> None:
        crud = next(
            r
            for r in validation_report.scenario_runs
            if r.scenario_id == SIMPLE_CRUD_SAAS.scenario_id and r.users == 100
        )
        ecommerce = next(
            r
            for r in validation_report.scenario_runs
            if r.scenario_id == "ecommerce" and r.users == 100
        )
        assert crud.total_monthly_cost_usd < ecommerce.total_monthly_cost_usd

    def test_formatter_produces_readable_output(self, validation_report) -> None:
        formatter = GcpPricingValidationSuiteFormatter()
        text = formatter.format_summary(validation_report)
        assert "GCP PRICING VALIDATION SUITE" in text
        assert "Expected cost range validation" in text

    def test_validation_script_runs(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--scenario",
                "self_esteem_habit",
                "--no-write",
            ],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "GCP PRICING VALIDATION SUITE" in result.stdout

    def test_validation_script_json_output(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--scenario",
                "simple_crud_saas",
                "--json",
                "--no-write",
            ],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert len(payload["scenario_runs"]) == 4
