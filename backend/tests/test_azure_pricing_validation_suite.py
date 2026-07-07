"""Tests for the Azure pricing validation suite."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.pricing.azure.scenarios import ALL_BENCHMARK_SCENARIOS, SELF_ESTEEM_HABIT
from app.pricing.azure.validation_suite import (
    AzurePricingValidationReportFormatter,
    AzurePricingValidationSuite,
    ValidationStatus,
)
from app.pricing.azure.verification import AzurePricingVerificationRunner
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS
from tests.azure_catalog_test_fixture import AzureCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "run_azure_pricing_validation.py"


@pytest.fixture
def validation_report():
    calculator = AzureCatalogTestFixture().build_cost_calculator()
    runner = AzurePricingVerificationRunner(calculator)
    return AzurePricingValidationSuite(runner).run()


class TestAzurePricingValidationSuite:
    def test_runs_all_scenarios_and_user_counts(self, validation_report) -> None:
        expected_runs = len(ALL_BENCHMARK_SCENARIOS) * len(BENCHMARK_USER_COUNTS)
        assert len(validation_report.scenario_runs) == expected_runs
        assert len(validation_report.scenario_assessments) == len(ALL_BENCHMARK_SCENARIOS)

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
            assert "cost_monotonicity" in rule_ids or run.users == BENCHMARK_USER_COUNTS[0]
            assert "total_equals_components" in rule_ids
            assert "no_negative_quantities" in rule_ids

    def test_no_silent_zero_failures(self, validation_report) -> None:
        failures = [
            check
            for run in validation_report.scenario_runs
            for check in run.validation_checks
            if check.rule_id == "no_silent_zero" and check.status == ValidationStatus.FAIL
        ]
        assert failures == []

    def test_assessments_have_category_scores(self, validation_report) -> None:
        for assessment in validation_report.scenario_assessments:
            scores = assessment.category_scores
            assert 1 <= scores.overall <= 10
            assert 1 <= scores.usage_assumptions <= 10
            assert 1 <= scores.catalog_price_mapping <= 10
            assert assessment.human_validation.review_summary
            assert assessment.realism_notes

    def test_expected_cost_ranges_defined_for_all_scenarios(self, validation_report) -> None:
        for run in validation_report.scenario_runs:
            assert run.expected_cost_range is not None
            assert run.expected_cost_range.in_range

    def test_static_website_scenario_present(self, validation_report) -> None:
        static_runs = [
            r for r in validation_report.scenario_runs if r.scenario_id == "static_website"
        ]
        assert len(static_runs) == len(BENCHMARK_USER_COUNTS)
        low = next(r for r in static_runs if r.users == 100)
        crud = next(
            r for r in validation_report.scenario_runs
            if r.scenario_id == "simple_crud_saas" and r.users == 100
        )
        assert low.total_monthly_cost_usd < crud.total_monthly_cost_usd

    def test_formatter_produces_readable_output(self, validation_report) -> None:
        formatter = AzurePricingValidationReportFormatter()
        text = formatter.format_suite_summary(validation_report)
        assert "AZURE PRICING VALIDATION SUITE" in text
        assert "Simple CRUD SaaS" in text
        assert "Expected cost range validation" in text

        run = validation_report.scenario_runs[0]
        run_text = formatter.format_run(run)
        assert "COMPONENT BREAKDOWN" in run_text
        assert "VALIDATION CHECKS" in run_text
        assert "HUMAN VALIDATION" in formatter.format_assessment(
            validation_report.scenario_assessments[0]
        )

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
        assert "AZURE PRICING VALIDATION SUITE" in result.stdout

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
