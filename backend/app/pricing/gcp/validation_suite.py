"""GCP pricing validation suite — simplified benchmark validation."""

from __future__ import annotations

import json
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS, USER_COUNT_TO_PROJECT_LABEL
from app.pricing.azure.scenarios import ALL_BENCHMARK_SCENARIOS, BenchmarkScenario, scenario_components
from app.pricing.gcp.expected_cost_ranges import evaluate_expected_cost
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.gcp.scenarios import normalize_gcp_service_aliases
from app.pricing.usage.service import InferenceMode


class ValidationStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ValidationCheckResult(BaseModel):
    rule_id: str
    rule_name: str
    status: ValidationStatus
    message: str
    details: list[str] = Field(default_factory=list)


class ExpectedCostRangeResult(BaseModel):
    users: int
    min_usd: float
    max_usd: float
    range_label: str
    actual_usd: float
    in_range: bool
    rationale: str = ""


class ScenarioRunReport(BaseModel):
    scenario_id: str
    scenario_name: str
    users: int
    total_monthly_cost_usd: float = 0.0
    cost_per_user_usd: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[str] = Field(default_factory=list)
    pricing_completeness: str = "complete"
    expected_cost_range: ExpectedCostRangeResult | None = None
    validation_checks: list[ValidationCheckResult] = Field(default_factory=list)


class GcpPricingValidationSuiteReport(BaseModel):
    inference_mode: str
    user_counts: list[int] = Field(default_factory=lambda: list(BENCHMARK_USER_COUNTS))
    scenario_runs: list[ScenarioRunReport] = Field(default_factory=list)
    suite_validation_summary: list[ValidationCheckResult] = Field(default_factory=list)


class GcpPricingValidationSuite:
    """Run benchmark scenarios with automated validation rules."""

    def __init__(self, pipeline: GcpProjectCostingPipeline) -> None:
        self._pipeline = pipeline

    def run(
        self,
        *,
        scenarios: Iterable[BenchmarkScenario] | None = None,
        inference_mode: InferenceMode = "heuristic",
    ) -> GcpPricingValidationSuiteReport:
        selected = list(scenarios or ALL_BENCHMARK_SCENARIOS)
        scenario_runs: list[ScenarioRunReport] = []

        for scenario in selected:
            components = scenario_components(scenario)
            for users in BENCHMARK_USER_COUNTS:
                scenario_runs.append(
                    self._run_scenario_at_users(
                        scenario,
                        components,
                        users,
                        inference_mode=inference_mode,
                    )
                )

        suite_summary = _suite_level_checks(scenario_runs)
        return GcpPricingValidationSuiteReport(
            inference_mode=inference_mode,
            scenario_runs=scenario_runs,
            suite_validation_summary=suite_summary,
        )

    def _run_scenario_at_users(
        self,
        scenario: BenchmarkScenario,
        components: list,
        users: int,
        *,
        inference_mode: InferenceMode,
    ) -> ScenarioRunReport:
        project = Project(
            name=scenario.name,
            description=scenario.product_description,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
            stage=scenario.stage,
        )
        for component in components:
            gcp_name = str(component.cloud.get("gcp", ""))
            resolved = normalize_gcp_service_aliases(gcp_name)
            if resolved != gcp_name:
                component.cloud = dict(component.cloud)
                component.cloud["gcp"] = resolved

        result = self._pipeline.calculate(
            project,
            components,
            feature_flags=scenario.feature_flags,
        )

        missing_prices = [
            f"{item.catalog_service_name}/{item.sku_key}: {item.reason}"
            for item in result.missing_prices
        ]
        total = round(result.total_usd, 4)
        cost_per_user = round(total / users, 6) if users else 0.0
        completeness = "complete" if not missing_prices else "incomplete"

        expected_range, in_range = evaluate_expected_cost(
            scenario.scenario_id,
            users,
            total,
        )
        expected_cost_result: ExpectedCostRangeResult | None = None
        if expected_range is not None and in_range is not None:
            expected_cost_result = ExpectedCostRangeResult(
                users=users,
                min_usd=expected_range.min_usd,
                max_usd=expected_range.max_usd,
                range_label=expected_range.label,
                actual_usd=total,
                in_range=in_range,
                rationale=expected_range.rationale,
            )

        run = ScenarioRunReport(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            users=users,
            total_monthly_cost_usd=total,
            cost_per_user_usd=cost_per_user,
            warnings=list(result.warnings),
            missing_prices=missing_prices,
            pricing_completeness=completeness,
            expected_cost_range=expected_cost_result,
        )
        run.validation_checks = _validate_run(run)
        return run


def _validate_run(run: ScenarioRunReport) -> list[ValidationCheckResult]:
    checks: list[ValidationCheckResult] = []

    if run.total_monthly_cost_usd < 0:
        checks.append(
            ValidationCheckResult(
                rule_id="non_negative_total",
                rule_name="Non-negative total cost",
                status=ValidationStatus.FAIL,
                message=f"Negative total cost: ${run.total_monthly_cost_usd:,.2f}",
            )
        )
    else:
        checks.append(
            ValidationCheckResult(
                rule_id="non_negative_total",
                rule_name="Non-negative total cost",
                status=ValidationStatus.PASS,
                message=f"Total cost ${run.total_monthly_cost_usd:,.2f} is non-negative.",
            )
        )

    if run.missing_prices:
        checks.append(
            ValidationCheckResult(
                rule_id="catalog_completeness",
                rule_name="Catalog price completeness",
                status=ValidationStatus.WARN,
                message=f"{len(run.missing_prices)} missing catalog price(s).",
                details=run.missing_prices[:5],
            )
        )
    else:
        checks.append(
            ValidationCheckResult(
                rule_id="catalog_completeness",
                rule_name="Catalog price completeness",
                status=ValidationStatus.PASS,
                message="All billable SKUs priced from catalog.",
            )
        )

    if run.expected_cost_range is not None:
        ec = run.expected_cost_range
        status = ValidationStatus.PASS if ec.in_range else ValidationStatus.WARN
        checks.append(
            ValidationCheckResult(
                rule_id="expected_cost_range",
                rule_name="Expected cost range",
                status=status,
                message=(
                    f"Actual ${ec.actual_usd:,.2f} "
                    f"{'within' if ec.in_range else 'outside'} expected {ec.range_label}."
                ),
            )
        )

    return checks


def _suite_level_checks(runs: list[ScenarioRunReport]) -> list[ValidationCheckResult]:
    fail_count = sum(
        1 for run in runs for check in run.validation_checks if check.status == ValidationStatus.FAIL
    )
    warn_count = sum(
        1 for run in runs for check in run.validation_checks if check.status == ValidationStatus.WARN
    )
    return [
        ValidationCheckResult(
            rule_id="suite_summary",
            rule_name="Suite validation summary",
            status=ValidationStatus.FAIL if fail_count else ValidationStatus.WARN if warn_count else ValidationStatus.PASS,
            message=f"{len(runs)} runs: {fail_count} fail(s), {warn_count} warn(s).",
        )
    ]


class GcpPricingValidationSuiteFormatter:
    """Text/JSON formatters for validation suite reports."""

    @staticmethod
    def format_summary(report: GcpPricingValidationSuiteReport) -> str:
        lines = [
            "=" * 80,
            "GCP PRICING VALIDATION SUITE — SUMMARY",
            "=" * 80,
            f"Inference mode: {report.inference_mode}",
            f"Total runs: {len(report.scenario_runs)}",
            "",
        ]
        for check in report.suite_validation_summary:
            icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(check.status.value, "?")
            lines.append(f"[{icon}] {check.rule_name}: {check.message}")
        lines.append("")
        lines.append("Expected cost range validation:")
        lines.append("-" * 80)
        for run in report.scenario_runs:
            if run.expected_cost_range is None:
                continue
            ec = run.expected_cost_range
            status = "OK" if ec.in_range else "WARN"
            lines.append(
                f"{run.scenario_name[:24]:<24} {run.users:>8,} "
                f"{ec.range_label:<18} ${ec.actual_usd:>10,.2f} {status:>6}"
            )
        return "\n".join(lines)

    @staticmethod
    def format_json(report: GcpPricingValidationSuiteReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2)
