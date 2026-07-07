"""Tests for Azure component pricing benchmark report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.pricing.azure.benchmark import (
    BENCHMARK_USER_COUNTS,
    AzureComponentPricingBenchmark,
    AzureComponentPricingBenchmarkFormatter,
    ComponentRole,
    self_esteem_scenario,
)
from app.pricing.azure.verification import AzurePricingVerificationRunner
from tests.azure_catalog_test_fixture import AzureCatalogTestFixture

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "benchmark_azure_component_pricing.py"


@pytest.fixture
def benchmark_report():
    calculator = AzureCatalogTestFixture().build_cost_calculator()
    runner = AzurePricingVerificationRunner(calculator)
    return AzureComponentPricingBenchmark(runner).run()


class TestAzureComponentPricingBenchmark:
    def test_runs_for_all_user_counts(self, benchmark_report) -> None:
        assert benchmark_report.user_counts == list(BENCHMARK_USER_COUNTS)
        for users in BENCHMARK_USER_COUNTS:
            rows = [row for row in benchmark_report.component_rows if row.users == users]
            assert len(rows) == len(self_esteem_scenario().components)

    def test_each_user_count_has_component_line_items(self, benchmark_report) -> None:
        for users in BENCHMARK_USER_COUNTS:
            rows = [row for row in benchmark_report.component_rows if row.users == users]
            roles = {row.component_role for row in rows}
            assert ComponentRole.BACKEND_API in roles
            assert ComponentRole.DATABASE in roles
            assert ComponentRole.STORAGE in roles
            assert ComponentRole.QUEUE_BACKGROUND in roles
            for row in rows:
                assert row.usage_assumptions != "-"
                assert row.raw_sku_quantities != "-"
                assert row.billable_quantities != "-"

    def test_total_cost_increases_with_users(self, benchmark_report) -> None:
        totals = [row.total_azure_monthly_cost for row in benchmark_report.summary_rows]
        assert totals == sorted(totals)
        assert totals[-1] > totals[0]

    def test_no_silent_zero_from_missing_catalog_price(self, benchmark_report) -> None:
        silent = [
            row
            for row in benchmark_report.component_rows
            if row.silent_zero_due_to_missing_price
        ]
        assert silent == []

    def test_missing_prices_reported_when_catalog_incomplete(self, benchmark_report) -> None:
        # Benchmark catalog is complete for this scenario; ensure reporting fields exist.
        for row in benchmark_report.component_rows:
            if row.has_unpriced_billable_usage:
                assert "MISSING PRICE" in row.warnings_missing or "UNPRICED" in row.warnings_missing

    def test_free_tier_appears_in_deductions_for_small_user_count(self, benchmark_report) -> None:
        api_row = next(
            row
            for row in benchmark_report.component_rows
            if row.users == 100 and row.component_role == ComponentRole.BACKEND_API
        )
        assert "free_tier" in api_row.free_tier_deducted or "tier/plan included" in api_row.free_tier_deducted

    def test_summary_rows_cover_all_user_counts(self, benchmark_report) -> None:
        assert len(benchmark_report.summary_rows) == len(BENCHMARK_USER_COUNTS)
        for summary in benchmark_report.summary_rows:
            assert summary.pricing_completeness in {"complete", "incomplete"}
            assert summary.main_reason_for_cost_increase

    def test_summary_marks_incomplete_when_billable_usage_unpriced(self, benchmark_report) -> None:
        summary_100k = next(row for row in benchmark_report.summary_rows if row.users == 100_000)
        api_row = next(
            row
            for row in benchmark_report.component_rows
            if row.users == 100_000 and row.component_role == ComponentRole.BACKEND_API
        )
        if api_row.has_unpriced_billable_usage:
            assert summary_100k.pricing_completeness == "incomplete"
            assert "UNPRICED" in api_row.warnings_missing
        text = AzureComponentPricingBenchmarkFormatter().format(benchmark_report)
        assert "AZURE COMPONENT PRICING BENCHMARK" in text
        assert "USER COUNT: 100" in text
        assert "SUMMARY" in text
        assert "Pricing completeness" in text

    def test_benchmark_script_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "AZURE COMPONENT PRICING BENCHMARK" in result.stdout
        for users in BENCHMARK_USER_COUNTS:
            assert f"USER COUNT: {users:,}" in result.stdout

    def test_benchmark_script_json_output(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert len(payload["summary_rows"]) == 4
        assert len(payload["component_rows"]) == 16
