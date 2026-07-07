"""Azure pricing validation suite — benchmark scenarios, rules, and reports."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.azure.benchmark import (
    BENCHMARK_USER_COUNTS,
    USER_COUNT_TO_PROJECT_LABEL,
    _dedupe_preserve_order,
    _fmt_scalar,
    _format_quantities,
    _format_unit_prices,
)
from app.pricing.azure.expected_cost_ranges import evaluate_expected_cost
from app.pricing.azure.human_validation import HumanValidationReview, get_human_validation
from app.pricing.azure.scenarios import (
    ALL_BENCHMARK_SCENARIOS,
    BenchmarkScenario,
    scenario_components,
)
from app.pricing.azure.usage_inference import InferenceMode
from app.pricing.azure.verification import (
    AzurePricingVerificationReport,
    AzurePricingVerificationRunner,
    ComponentVerificationReport,
)
from app.pricing.schemas import UsageAssumption

# Keys whose per-user rate should stay stable across user counts.
_PER_USER_RATE_KEYS: dict[str, str] = {
    "requests_per_month": "requests/user/month",
    "executions_per_month": "executions/user/month",
    "storage_gb": "GB/user",
    "backup_storage_gb": "GB/user/month",
    "write_operations": "writes/user/month",
    "read_operations": "reads/user/month",
    "queue_operations": "messages/user/month",
    "network_egress_gb": "GB/user/month",
    "data_egress_gb": "GB/user/month",
}

# Config keys allowed to differ across scales (tier minimums, replica counts).
_SCALE_DEPENDENT_KEYS = frozenset(
    {
        "min_replicas",
        "max_replicas",
        "tier",
        "compute_model",
        "vcores",
        "hours_per_month",
        "plan",
        "messaging_tier",
        "messaging_units",
        "brokered_connections",
    }
)

_MAX_COST_PER_USER_USD = 500.0
_MIN_COST_PER_USER_USD = 0.0
_COMPONENT_DOMINANCE_THRESHOLD = 0.95
_PER_USER_RATE_TOLERANCE = 0.05


class ValidationStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ValidationCheckResult(BaseModel):
    """Outcome of one automated validation rule."""

    rule_id: str
    rule_name: str
    status: ValidationStatus
    message: str
    details: list[str] = Field(default_factory=list)


class UsageAssumptionDetail(BaseModel):
    """Structured usage assumption for reports."""

    key: str
    value: int | float | str | bool
    unit: str | None = None
    source: str | None = None
    confidence: str | None = None
    reasoning: str | None = None
    category: str = "inferred"


class ComponentRunDetail(BaseModel):
    """Component breakdown for one scenario run."""

    component_id: str
    component_name: str
    azure_service: str
    per_user_behavior: list[UsageAssumptionDetail] = Field(default_factory=list)
    inferred_assumptions: list[UsageAssumptionDetail] = Field(default_factory=list)
    raw_sku_quantities: str = "-"
    free_tier_deduction: str = "-"
    included_usage_deduction: str = "-"
    billable_quantities: str = "-"
    unit_prices: str = "-"
    monthly_component_cost: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[str] = Field(default_factory=list)


class ExpectedCostRangeResult(BaseModel):
    """Expected vs actual cost for one run."""

    users: int
    min_usd: float
    max_usd: float
    range_label: str
    actual_usd: float
    in_range: bool
    rationale: str = ""


class PipelineCategoryScores(BaseModel):
    """Per-pipeline-stage quality scores (1–10)."""

    usage_assumptions: int = Field(ge=1, le=10)
    azure_service_selection: int = Field(ge=1, le=10)
    sku_quantity_calculation: int = Field(ge=1, le=10)
    free_tier_included_usage: int = Field(ge=1, le=10)
    catalog_price_mapping: int = Field(ge=1, le=10)
    overall: int = Field(ge=1, le=10)


class ScenarioRunReport(BaseModel):
    """Full report for one scenario at one user count."""

    scenario_id: str
    scenario_name: str
    users: int
    architecture_summary: str
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    components: list[ComponentRunDetail] = Field(default_factory=list)
    total_monthly_cost_usd: float = 0.0
    cost_per_user_usd: float = 0.0
    largest_cost_drivers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[str] = Field(default_factory=list)
    pricing_completeness: str = "complete"
    expected_cost_range: ExpectedCostRangeResult | None = None
    validation_checks: list[ValidationCheckResult] = Field(default_factory=list)


class ScenarioAssessment(BaseModel):
    """Qualitative assessment for one scenario across all user counts."""

    scenario_id: str
    scenario_name: str
    looks_realistic: bool
    realism_notes: str
    highest_impact_assumptions: list[str] = Field(default_factory=list)
    assumptions_to_refine: list[str] = Field(default_factory=list)
    category_scores: PipelineCategoryScores
    human_validation: HumanValidationReview
    expected_cost_results: list[ExpectedCostRangeResult] = Field(default_factory=list)
    recommended_improvements: list[str] = Field(default_factory=list)
    validation_pass_count: int = 0
    validation_warn_count: int = 0
    validation_fail_count: int = 0


class AzurePricingValidationSuiteReport(BaseModel):
    """Complete validation suite output."""

    inference_mode: str
    user_counts: list[int] = Field(default_factory=lambda: list(BENCHMARK_USER_COUNTS))
    scenario_runs: list[ScenarioRunReport] = Field(default_factory=list)
    scenario_assessments: list[ScenarioAssessment] = Field(default_factory=list)
    suite_validation_summary: list[ValidationCheckResult] = Field(default_factory=list)


class AzurePricingValidationSuite:
    """Run all benchmark scenarios with automated validation rules."""

    def __init__(self, verification_runner: AzurePricingVerificationRunner) -> None:
        self._runner = verification_runner

    def run(
        self,
        *,
        scenarios: Iterable[BenchmarkScenario] | None = None,
        inference_mode: InferenceMode = "heuristic",
    ) -> AzurePricingValidationSuiteReport:
        selected = list(scenarios or ALL_BENCHMARK_SCENARIOS)
        scenario_runs: list[ScenarioRunReport] = []
        runs_by_scenario: dict[str, list[ScenarioRunReport]] = {}

        for scenario in selected:
            runs_by_scenario[scenario.scenario_id] = []
            previous: ScenarioRunReport | None = None
            scenario_run_list: list[ScenarioRunReport] = []
            for users in BENCHMARK_USER_COUNTS:
                run = self._run_scenario_at_users(
                    scenario,
                    users,
                    inference_mode=inference_mode,
                    previous_run=previous,
                )
                scenario_run_list.append(run)
                previous = run

            cross_check = _check_per_user_behavior_consistent(scenario_run_list)
            for index, run in enumerate(scenario_run_list):
                merged = list(run.validation_checks)
                if not any(c.rule_id == cross_check.rule_id for c in merged):
                    merged.append(cross_check)
                scenario_run_list[index] = run.model_copy(update={"validation_checks": merged})

            scenario_runs.extend(scenario_run_list)
            runs_by_scenario[scenario.scenario_id] = scenario_run_list

        assessments = [
            _assess_scenario(scenario, runs_by_scenario[scenario.scenario_id])
            for scenario in selected
        ]
        suite_summary = _suite_level_checks(scenario_runs)

        return AzurePricingValidationSuiteReport(
            inference_mode=inference_mode,
            scenario_runs=scenario_runs,
            scenario_assessments=assessments,
            suite_validation_summary=suite_summary,
        )

    def _run_scenario_at_users(
        self,
        scenario: BenchmarkScenario,
        users: int,
        *,
        inference_mode: InferenceMode,
        previous_run: ScenarioRunReport | None,
    ) -> ScenarioRunReport:
        project = Project(
            name=scenario.name,
            description=scenario.product_description,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
            stage=scenario.stage,
        )
        components = scenario_components(scenario)
        verification = self._runner.run(
            project,
            components,
            feature_flags=scenario.feature_flags,
            inference_mode=inference_mode,
        )

        component_details = [
            _component_detail_from_verification(component) for component in verification.components
        ]
        missing_prices = _collect_missing_prices(verification)
        warnings = _dedupe_preserve_order(list(verification.warnings))
        for detail in component_details:
            warnings.extend(detail.warnings)
            missing_prices.extend(detail.missing_prices)
        warnings = _dedupe_preserve_order(warnings)
        missing_prices = _dedupe_preserve_order(missing_prices)

        total = round(verification.total_usd, 4)
        cost_per_user = round(total / users, 6) if users else 0.0
        completeness = "complete" if not missing_prices else "incomplete"
        drivers = _largest_cost_drivers(component_details, total)

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
            architecture_summary=scenario.expected_architecture,
            feature_flags=dict(scenario.feature_flags),
            components=component_details,
            total_monthly_cost_usd=total,
            cost_per_user_usd=cost_per_user,
            largest_cost_drivers=drivers,
            warnings=warnings,
            missing_prices=missing_prices,
            pricing_completeness=completeness,
            expected_cost_range=expected_cost_result,
        )
        run.validation_checks = _validate_run(run, verification, previous_run=previous_run)
        return run


def _component_detail_from_verification(
    component: ComponentVerificationReport,
) -> ComponentRunDetail:
    per_user = [
        _assumption_detail(item, category="per-user behavior")
        for item in component.behavioral_assumptions
    ]
    inferred = [
        _assumption_detail(item, category="inferred")
        for item in component.resolved_assumptions
        if item.key not in {a.key for a in component.behavioral_assumptions}
    ]

    warnings: list[str] = []
    missing: list[str] = []
    for line in component.sku_lines:
        if line.billable_quantity > 0 and line.sku_cost_usd is None:
            if line.missing_price_reason:
                missing.append(f"{line.sku_key}: {line.missing_price_reason}")
            else:
                missing.append(f"{line.sku_key}: unpriced billable usage")
    warnings.extend(_dedupe_preserve_order(component.warnings))

    return ComponentRunDetail(
        component_id=component.architecture.component_id,
        component_name=component.architecture.component_name,
        azure_service=component.azure_service,
        per_user_behavior=per_user,
        inferred_assumptions=inferred,
        raw_sku_quantities=_format_quantities(component.raw_sku_quantities, use_raw=True),
        free_tier_deduction=_format_free_tier(component),
        included_usage_deduction=_format_included_usage(component),
        billable_quantities=_format_quantities(component.billable_sku_quantities, use_raw=False),
        unit_prices=_format_unit_prices(component.sku_lines),
        monthly_component_cost=round(component.subtotal_usd, 4),
        warnings=warnings,
        missing_prices=missing,
    )


def _assumption_detail(item: UsageAssumption, *, category: str) -> UsageAssumptionDetail:
    return UsageAssumptionDetail(
        key=item.key,
        value=item.value,
        unit=item.unit,
        source=item.source.value if item.source else None,
        confidence=item.confidence.value if item.confidence else None,
        reasoning=item.reasoning,
        category=category,
    )


def _format_free_tier(component: ComponentVerificationReport) -> str:
    parts: list[str] = []
    for line in component.sku_lines:
        if line.free_tier_deducted > 0:
            parts.append(f"{line.sku_key}: free_tier={_fmt_scalar(line.free_tier_deducted)}")
    return "; ".join(parts) if parts else "-"


def _format_included_usage(component: ComponentVerificationReport) -> str:
    parts: list[str] = []
    for item in component.included_usage:
        parts.append(
            f"{item['sku_key']}: tier/plan included {_fmt_scalar(item['quantity'])} {item['unit']}"
        )
    for line in component.sku_lines:
        if line.tier_included_quantity > 0:
            parts.append(
                f"{line.sku_key}: tier_included={_fmt_scalar(line.tier_included_quantity)}"
            )
    return "; ".join(parts) if parts else "-"


def _collect_missing_prices(report: AzurePricingVerificationReport) -> list[str]:
    items: list[str] = []
    for item in report.missing_prices:
        items.append(f"{item.catalog_service_name}/{item.sku_key}: {item.reason}")
    return items


def _largest_cost_drivers(components: list[ComponentRunDetail], total: float) -> list[str]:
    if total <= 0:
        return ["(no billable cost)"]
    ranked = sorted(components, key=lambda item: item.monthly_component_cost, reverse=True)
    drivers: list[str] = []
    for item in ranked[:3]:
        if item.monthly_component_cost <= 0:
            continue
        share = item.monthly_component_cost / total * 100
        drivers.append(
            f"{item.component_name} ({item.azure_service}): "
            f"${item.monthly_component_cost:,.2f} ({share:.1f}%)"
        )
    return drivers or ["(no billable cost)"]


def _validate_run(
    run: ScenarioRunReport,
    verification: AzurePricingVerificationReport,
    *,
    previous_run: ScenarioRunReport | None,
) -> list[ValidationCheckResult]:
    checks: list[ValidationCheckResult] = []

    checks.append(_check_cost_monotonicity(run, previous_run))
    checks.append(_check_total_equals_components(run, verification))
    checks.append(_check_no_negative_quantities(verification))
    checks.append(_check_no_silent_zero(verification))
    checks.append(_check_missing_prices_reported(run))
    checks.append(_check_catalog_prices_exist(verification))
    checks.append(_check_free_tier_applied(verification, run.users))
    checks.append(_check_included_usage_applied(verification))
    checks.append(_check_no_sku_silently_ignored(verification))
    checks.append(_check_component_cost_reasonable(run))
    checks.append(_check_cost_per_user_reasonable(run))
    checks.append(_check_expected_cost_range(run))

    return checks


def _check_expected_cost_range(run: ScenarioRunReport) -> ValidationCheckResult:
    result = run.expected_cost_range
    if result is None:
        return ValidationCheckResult(
            rule_id="expected_cost_range",
            rule_name="Expected cost range",
            status=ValidationStatus.PASS,
            message="No expected range defined for this scenario/user count.",
        )
    if result.in_range:
        return ValidationCheckResult(
            rule_id="expected_cost_range",
            rule_name="Expected cost range",
            status=ValidationStatus.PASS,
            message=(
                f"Actual ${result.actual_usd:,.2f} is within expected "
                f"{result.range_label}/mo."
            ),
        )
    direction = "below" if result.actual_usd < result.min_usd else "above"
    return ValidationCheckResult(
        rule_id="expected_cost_range",
        rule_name="Expected cost range",
        status=ValidationStatus.WARN,
        message=(
            f"Actual ${result.actual_usd:,.2f} is {direction} expected "
            f"{result.range_label}/mo."
        ),
        details=[result.rationale] if result.rationale else [],
    )


def _check_cost_monotonicity(
    run: ScenarioRunReport,
    previous: ScenarioRunReport | None,
) -> ValidationCheckResult:
    if previous is None:
        return ValidationCheckResult(
            rule_id="cost_monotonicity",
            rule_name="Costs increase consistently with user count",
            status=ValidationStatus.PASS,
            message="Baseline user count — monotonicity not applicable.",
        )
    if run.total_monthly_cost_usd >= previous.total_monthly_cost_usd - 0.01:
        return ValidationCheckResult(
            rule_id="cost_monotonicity",
            rule_name="Costs increase consistently with user count",
            status=ValidationStatus.PASS,
            message=(
                f"Total ${run.total_monthly_cost_usd:,.2f} >= "
                f"${previous.total_monthly_cost_usd:,.2f} at {previous.users:,} users."
            ),
        )
    return ValidationCheckResult(
        rule_id="cost_monotonicity",
        rule_name="Costs increase consistently with user count",
        status=ValidationStatus.FAIL,
        message=(
            f"Total decreased from ${previous.total_monthly_cost_usd:,.2f} "
            f"({previous.users:,} users) to ${run.total_monthly_cost_usd:,.2f} "
            f"({run.users:,} users)."
        ),
    )


def _check_total_equals_components(
    run: ScenarioRunReport,
    verification: AzurePricingVerificationReport,
) -> ValidationCheckResult:
    component_sum = round(sum(item.monthly_component_cost for item in run.components), 4)
    delta = abs(component_sum - run.total_monthly_cost_usd)
    if delta <= 0.01:
        return ValidationCheckResult(
            rule_id="total_equals_components",
            rule_name="Total equals sum of component costs",
            status=ValidationStatus.PASS,
            message=f"Component sum ${component_sum:,.4f} matches total.",
        )
    return ValidationCheckResult(
        rule_id="total_equals_components",
        rule_name="Total equals sum of component costs",
        status=ValidationStatus.FAIL,
        message=(
            f"Component sum ${component_sum:,.4f} != total "
            f"${run.total_monthly_cost_usd:,.4f} (delta ${delta:,.4f})."
        ),
        details=[f"verification.total_usd={verification.total_usd}"],
    )


def _check_no_negative_quantities(
    verification: AzurePricingVerificationReport,
) -> ValidationCheckResult:
    negatives: list[str] = []
    for component in verification.components:
        for line in component.sku_lines:
            if line.raw_quantity is not None and line.raw_quantity < 0:
                negatives.append(f"{component.architecture.component_id}/{line.sku_key}: raw")
            if line.billable_quantity < 0:
                negatives.append(
                    f"{component.architecture.component_id}/{line.sku_key}: billable"
                )
            if line.free_tier_deducted < 0:
                negatives.append(
                    f"{component.architecture.component_id}/{line.sku_key}: free_tier"
                )
    if not negatives:
        return ValidationCheckResult(
            rule_id="no_negative_quantities",
            rule_name="No negative quantities",
            status=ValidationStatus.PASS,
            message="All SKU quantities are non-negative.",
        )
    return ValidationCheckResult(
        rule_id="no_negative_quantities",
        rule_name="No negative quantities",
        status=ValidationStatus.FAIL,
        message=f"{len(negatives)} negative quantity value(s) found.",
        details=negatives,
    )


def _check_no_silent_zero(verification: AzurePricingVerificationReport) -> ValidationCheckResult:
    silent: list[str] = []
    for component in verification.components:
        unpriced = sum(
            1
            for line in component.sku_lines
            if line.billable_quantity > 0 and line.sku_cost_usd is None
        )
        has_billable = any(line.billable_quantity > 0 for line in component.sku_lines)
        if has_billable and component.subtotal_usd == 0 and unpriced > 0:
            silent.append(component.architecture.component_id)
    if not silent:
        return ValidationCheckResult(
            rule_id="no_silent_zero",
            rule_name="No SKU silently ignored (silent $0)",
            status=ValidationStatus.PASS,
            message="No component has billable usage priced at $0 due to missing catalog entries.",
        )
    return ValidationCheckResult(
        rule_id="no_silent_zero",
        rule_name="No SKU silently ignored (silent $0)",
        status=ValidationStatus.FAIL,
        message=f"Silent $0 on components: {', '.join(silent)}",
        details=silent,
    )


def _check_missing_prices_reported(run: ScenarioRunReport) -> ValidationCheckResult:
    if not run.missing_prices:
        return ValidationCheckResult(
            rule_id="missing_prices_reported",
            rule_name="Missing catalog prices are reported",
            status=ValidationStatus.PASS,
            message="No missing catalog prices.",
        )
    return ValidationCheckResult(
        rule_id="missing_prices_reported",
        rule_name="Missing catalog prices are reported",
        status=ValidationStatus.WARN,
        message=f"{len(run.missing_prices)} missing price(s) reported.",
        details=run.missing_prices,
    )


def _check_catalog_prices_exist(
    verification: AzurePricingVerificationReport,
) -> ValidationCheckResult:
    unpriced: list[str] = []
    for component in verification.components:
        for line in component.sku_lines:
            if line.billable_quantity > 0 and line.unit_price_usd is None:
                unpriced.append(
                    f"{component.azure_service}/{line.sku_key}"
                    + (f": {line.missing_price_reason}" if line.missing_price_reason else "")
                )
    if not unpriced:
        return ValidationCheckResult(
            rule_id="catalog_prices_exist",
            rule_name="Every priced SKU exists in catalog",
            status=ValidationStatus.PASS,
            message="All billable SKUs have catalog unit prices.",
        )
    return ValidationCheckResult(
        rule_id="catalog_prices_exist",
        rule_name="Every priced SKU exists in catalog",
        status=ValidationStatus.FAIL,
        message=f"{len(unpriced)} billable SKU(s) missing catalog prices.",
        details=unpriced,
    )


def _check_free_tier_applied(
    verification: AzurePricingVerificationReport,
    users: int,
) -> ValidationCheckResult:
    deductions: list[str] = []
    for component in verification.components:
        for line in component.sku_lines:
            if line.free_tier_deducted > 0:
                deductions.append(f"{component.architecture.component_id}/{line.sku_key}")
    if deductions:
        return ValidationCheckResult(
            rule_id="free_tier_applied",
            rule_name="Free tier is applied correctly",
            status=ValidationStatus.PASS,
            message=f"Free tier deductions applied to {len(deductions)} SKU line(s).",
            details=deductions,
        )
    if users <= 1_000:
        return ValidationCheckResult(
            rule_id="free_tier_applied",
            rule_name="Free tier is applied correctly",
            status=ValidationStatus.WARN,
            message="No free tier deductions at low user count — verify allowances are configured.",
        )
    return ValidationCheckResult(
        rule_id="free_tier_applied",
        rule_name="Free tier is applied correctly",
        status=ValidationStatus.PASS,
        message="No free tier deductions (usage exceeds allowances at this scale).",
    )


def _check_included_usage_applied(
    verification: AzurePricingVerificationReport,
) -> ValidationCheckResult:
    inclusions: list[str] = []
    for component in verification.components:
        for item in component.included_usage:
            inclusions.append(f"{component.architecture.component_id}/{item['sku_key']}")
        for line in component.sku_lines:
            if line.tier_included_quantity > 0:
                inclusions.append(
                    f"{component.architecture.component_id}/{line.sku_key}:tier"
                )
    if inclusions:
        return ValidationCheckResult(
            rule_id="included_usage_applied",
            rule_name="Included usage is applied correctly",
            status=ValidationStatus.PASS,
            message=f"Included usage applied on {len(inclusions)} SKU line(s).",
            details=inclusions,
        )
    return ValidationCheckResult(
        rule_id="included_usage_applied",
        rule_name="Included usage is applied correctly",
        status=ValidationStatus.PASS,
        message="No tier/plan included usage deductions (none configured or all usage billable).",
    )


def _check_no_sku_silently_ignored(
    verification: AzurePricingVerificationReport,
) -> ValidationCheckResult:
    ignored: list[str] = []
    for component in verification.components:
        raw_keys = {item.sku_key for item in component.raw_sku_quantities}
        line_keys = {line.sku_key for line in component.sku_lines}
        missing = raw_keys - line_keys
        for key in sorted(missing):
            ignored.append(f"{component.architecture.component_id}/{key}")
    if not ignored:
        return ValidationCheckResult(
            rule_id="no_sku_ignored",
            rule_name="No SKU is silently ignored",
            status=ValidationStatus.PASS,
            message="Every raw SKU appears in the verification trace.",
        )
    return ValidationCheckResult(
        rule_id="no_sku_ignored",
        rule_name="No SKU is silently ignored",
        status=ValidationStatus.FAIL,
        message=f"{len(ignored)} raw SKU(s) missing from cost trace.",
        details=ignored,
    )


def _check_component_cost_reasonable(run: ScenarioRunReport) -> ValidationCheckResult:
    if run.total_monthly_cost_usd <= 0:
        return ValidationCheckResult(
            rule_id="component_cost_reasonable",
            rule_name="Cost per component is reasonable",
            status=ValidationStatus.WARN,
            message="Total cost is $0 — verify this is expected for the scenario.",
        )
    dominant: list[str] = []
    for item in run.components:
        share = item.monthly_component_cost / run.total_monthly_cost_usd
        if share > _COMPONENT_DOMINANCE_THRESHOLD and len(run.components) > 1:
            dominant.append(
                f"{item.component_name} is {share * 100:.1f}% of total "
                f"(${item.monthly_component_cost:,.2f})"
            )
    if dominant:
        return ValidationCheckResult(
            rule_id="component_cost_reasonable",
            rule_name="Cost per component is reasonable",
            status=ValidationStatus.WARN,
            message="One component dominates total cost — review assumptions.",
            details=dominant,
        )
    return ValidationCheckResult(
        rule_id="component_cost_reasonable",
        rule_name="Cost per component is reasonable",
        status=ValidationStatus.PASS,
        message="No single component exceeds 95% of total cost.",
    )


def _check_cost_per_user_reasonable(run: ScenarioRunReport) -> ValidationCheckResult:
    cpu = run.cost_per_user_usd
    if cpu > _MAX_COST_PER_USER_USD:
        return ValidationCheckResult(
            rule_id="cost_per_user_reasonable",
            rule_name="Cost per user is reasonable",
            status=ValidationStatus.WARN,
            message=f"Cost per user ${cpu:,.4f} exceeds ${_MAX_COST_PER_USER_USD:,.2f}/user.",
        )
    return ValidationCheckResult(
        rule_id="cost_per_user_reasonable",
        rule_name="Cost per user is reasonable",
        status=ValidationStatus.PASS,
        message=f"Cost per user ${cpu:,.4f} is within expected bounds.",
    )


def _check_per_user_behavior_consistent(
    all_runs: list[ScenarioRunReport],
) -> ValidationCheckResult:
    if len(all_runs) < 2:
        return ValidationCheckResult(
            rule_id="per_user_behavior_consistent",
            rule_name="Per-user behavior consistent across scales",
            status=ValidationStatus.PASS,
            message="Insufficient runs for cross-scale comparison.",
        )

    drift: list[str] = []
    baseline = all_runs[0]
    for other in all_runs[1:]:
        for base_comp in baseline.components:
            other_comp = next(
                (c for c in other.components if c.component_id == base_comp.component_id),
                None,
            )
            if other_comp is None:
                continue
            base_rates = _derived_per_user_rates(base_comp, baseline.users)
            other_rates = _derived_per_user_rates(other_comp, other.users)
            for key, base_rate in base_rates.items():
                other_rate = other_rates.get(key)
                if other_rate is None:
                    continue
                if base_rate <= 0:
                    continue
                delta = abs(other_rate - base_rate) / base_rate
                if delta > _PER_USER_RATE_TOLERANCE:
                    drift.append(
                        f"{base_comp.component_id}/{key}: "
                        f"{base_rate:.4g} vs {other_rate:.4g} at {other.users:,} users "
                        f"({delta * 100:.1f}% drift)"
                    )

    if not drift:
        return ValidationCheckResult(
            rule_id="per_user_behavior_consistent",
            rule_name="Per-user behavior consistent across scales",
            status=ValidationStatus.PASS,
            message="Derived per-user rates stable across all user counts.",
        )
    return ValidationCheckResult(
        rule_id="per_user_behavior_consistent",
        rule_name="Per-user behavior consistent across scales",
        status=ValidationStatus.WARN,
        message=f"{len(drift)} per-user rate drift(s) detected.",
        details=drift[:10],
    )


def _derived_per_user_rates(
    component: ComponentRunDetail,
    users: int,
) -> dict[str, float]:
    if users <= 0:
        return {}
    rates: dict[str, float] = {}
    for item in component.per_user_behavior:
        if isinstance(item.value, (int, float)):
            rates[item.key] = float(item.value)
    for item in component.inferred_assumptions:
        if item.key in _SCALE_DEPENDENT_KEYS:
            continue
        if not isinstance(item.value, (int, float)):
            continue
        rate_key = _PER_USER_RATE_KEYS.get(item.key)
        if rate_key:
            rates[item.key] = float(item.value) / users
    return rates


def _assess_scenario(
    scenario: BenchmarkScenario,
    runs: list[ScenarioRunReport],
) -> ScenarioAssessment:
    pass_count = sum(
        1 for run in runs for check in run.validation_checks if check.status == ValidationStatus.PASS
    )
    warn_count = sum(
        1 for run in runs for check in run.validation_checks if check.status == ValidationStatus.WARN
    )
    fail_count = sum(
        1 for run in runs for check in run.validation_checks if check.status == ValidationStatus.FAIL
    )

    totals = [run.total_monthly_cost_usd for run in runs]
    monotonic = all(
        totals[i] <= totals[i + 1] + 0.01 for i in range(len(totals) - 1)
    )
    incomplete = any(run.pricing_completeness == "incomplete" for run in runs)
    has_missing = any(run.missing_prices for run in runs)
    out_of_range = sum(
        1
        for run in runs
        if run.expected_cost_range is not None and not run.expected_cost_range.in_range
    )

    human = get_human_validation(scenario.scenario_id)
    if human is None:
        human = HumanValidationReview(
            scenario_id=scenario.scenario_id,
            looks_realistic=monotonic and fail_count == 0,
            realism_explanation="No curated human review available for this scenario.",
            largest_cost_drivers=tuple(),
            highest_impact_assumptions=tuple(),
            assumptions_to_refine=tuple(),
            service_selection_score=5,
            review_summary="Pending engineering review.",
        )

    looks_realistic = human.looks_realistic and monotonic and fail_count == 0 and out_of_range == 0
    realism_notes_parts: list[str] = []
    if monotonic:
        realism_notes_parts.append(
            f"Costs grow from ${totals[0]:,.2f}/mo ({runs[0].users:,} users) "
            f"to ${totals[-1]:,.2f}/mo ({runs[-1].users:,} users)."
        )
    else:
        realism_notes_parts.append("Cost curve is not monotonic — review scaling assumptions.")
    if incomplete:
        realism_notes_parts.append("Pricing completeness is incomplete due to missing catalog entries.")
    if out_of_range:
        realism_notes_parts.append(
            f"{out_of_range} user scale(s) fall outside expected cost ranges."
        )

    expected_results = [
        run.expected_cost_range for run in runs if run.expected_cost_range is not None
    ]
    category_scores = _pipeline_category_scores(
        runs,
        human=human,
        fail_count=fail_count,
        warn_count=warn_count,
        has_missing=has_missing,
        out_of_range=out_of_range,
    )
    improvements = _recommended_improvements(scenario, runs, fail_count, warn_count, out_of_range)

    return ScenarioAssessment(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        looks_realistic=looks_realistic,
        realism_notes=" ".join(realism_notes_parts),
        highest_impact_assumptions=list(human.highest_impact_assumptions),
        assumptions_to_refine=list(human.assumptions_to_refine),
        category_scores=category_scores,
        human_validation=human,
        expected_cost_results=expected_results,
        recommended_improvements=improvements,
        validation_pass_count=pass_count,
        validation_warn_count=warn_count,
        validation_fail_count=fail_count,
    )


def _pipeline_category_scores(
    runs: list[ScenarioRunReport],
    *,
    human: HumanValidationReview,
    fail_count: int,
    warn_count: int,
    has_missing: bool,
    out_of_range: int,
) -> PipelineCategoryScores:
    usage = _score_checks(
        runs,
        {"per_user_behavior_consistent"},
        base=9,
        warn_penalty=1,
        fail_penalty=3,
    )
    sku = _score_checks(
        runs,
        {"total_equals_components", "no_negative_quantities", "no_sku_ignored"},
        base=10,
        warn_penalty=2,
        fail_penalty=4,
    )
    free_tier = _score_checks(
        runs,
        {"free_tier_applied", "included_usage_applied"},
        base=9,
        warn_penalty=1,
        fail_penalty=3,
    )
    catalog = _score_checks(
        runs,
        {
            "catalog_prices_exist",
            "missing_prices_reported",
            "no_silent_zero",
        },
        base=10,
        warn_penalty=1,
        fail_penalty=4,
    )
    if has_missing:
        catalog = min(catalog, 5)
    if out_of_range:
        usage = min(usage, max(1, usage - out_of_range))

    service = human.service_selection_score
    overall = round((usage + service + sku + free_tier + catalog) / 5)
    overall = max(1, min(10, overall))
    if fail_count:
        overall = max(1, overall - min(3, fail_count))

    return PipelineCategoryScores(
        usage_assumptions=usage,
        azure_service_selection=service,
        sku_quantity_calculation=sku,
        free_tier_included_usage=free_tier,
        catalog_price_mapping=catalog,
        overall=overall,
    )


def _score_checks(
    runs: list[ScenarioRunReport],
    rule_ids: set[str],
    *,
    base: int,
    warn_penalty: int,
    fail_penalty: int,
) -> int:
    score = base
    for run in runs:
        for check in run.validation_checks:
            if check.rule_id not in rule_ids:
                continue
            if check.status == ValidationStatus.WARN:
                score -= warn_penalty
            elif check.status == ValidationStatus.FAIL:
                score -= fail_penalty
    return max(1, min(10, score))


def _recommended_improvements(
    scenario: BenchmarkScenario,
    runs: list[ScenarioRunReport],
    fail_count: int,
    warn_count: int,
    out_of_range: int,
) -> list[str]:
    items: list[str] = []
    if fail_count:
        items.append("Fix validation failures before using estimates in production UI.")
    if any(run.missing_prices for run in runs):
        items.append("Sync azure_catalog meters for all SKUs referenced by this architecture.")
    if out_of_range:
        items.append(
            "Review usage assumptions or update expected cost ranges after intentional model changes."
        )
    if scenario.feature_flags.get("ai"):
        items.append("Add LLM inference path benchmarks and external AI API cost passthrough.")
    if warn_count:
        items.append("Review heuristic usage_model_builder defaults for this product type.")
    items.append("Re-run validation suite after pricing engine changes to detect regressions.")
    return items


def _suite_level_checks(runs: list[ScenarioRunReport]) -> list[ValidationCheckResult]:
    total_runs = len(runs)
    failed = sum(
        1
        for run in runs
        for check in run.validation_checks
        if check.status == ValidationStatus.FAIL
    )
    warned = sum(
        1
        for run in runs
        for check in run.validation_checks
        if check.status == ValidationStatus.WARN
    )
    status = ValidationStatus.PASS
    if failed:
        status = ValidationStatus.FAIL
    elif warned:
        status = ValidationStatus.WARN
    return [
        ValidationCheckResult(
            rule_id="suite_complete",
            rule_name="Validation suite completed",
            status=ValidationStatus.PASS,
            message=f"Executed {total_runs} scenario runs across {len(ALL_BENCHMARK_SCENARIOS)} scenarios.",
        ),
        ValidationCheckResult(
            rule_id="suite_quality",
            rule_name="Overall validation quality",
            status=status,
            message=f"{failed} failure(s), {warned} warning(s) across all checks.",
        ),
    ]


class AzurePricingValidationReportFormatter:
    """Render validation suite reports as human-readable text."""

    def format_run(self, run: ScenarioRunReport) -> str:
        lines: list[str] = []
        lines.append("=" * 100)
        lines.append(f"SCENARIO: {run.scenario_name}")
        lines.append(f"USERS: {run.users:,}")
        lines.append(f"ARCHITECTURE: {run.architecture_summary}")
        lines.append(f"Feature flags: {json.dumps(run.feature_flags, sort_keys=True)}")
        lines.append("")

        lines.append("USAGE ASSUMPTIONS")
        lines.append("-" * 100)
        for component in run.components:
            lines.append(f"\n  [{component.component_name}] ({component.azure_service})")
            if component.per_user_behavior:
                lines.append("  Per-user behavior:")
                for item in component.per_user_behavior:
                    lines.append(self._format_assumption_line(item))
            else:
                lines.append("  Per-user behavior: (derived by heuristic usage model)")
            if component.inferred_assumptions:
                lines.append("  Inferred assumptions:")
                for item in component.inferred_assumptions:
                    lines.append(self._format_assumption_line(item))

        lines.append("")
        lines.append("COMPONENT BREAKDOWN")
        lines.append("-" * 100)
        for component in run.components:
            lines.append(f"\n  {component.component_name} — {component.azure_service}")
            lines.append(f"    Raw SKU quantities:      {component.raw_sku_quantities}")
            lines.append(f"    Free tier deduction:     {component.free_tier_deduction}")
            lines.append(f"    Included usage deducted: {component.included_usage_deduction}")
            lines.append(f"    Billable quantities:     {component.billable_quantities}")
            lines.append(f"    Unit prices:             {component.unit_prices}")
            lines.append(f"    Monthly component cost:  ${component.monthly_component_cost:,.4f}")
            if component.warnings:
                lines.append(f"    Warnings: {' | '.join(component.warnings)}")
            if component.missing_prices:
                lines.append(f"    Missing prices: {' | '.join(component.missing_prices)}")

        lines.append("")
        lines.append("PROJECT SUMMARY")
        lines.append("-" * 100)
        lines.append(f"  Total monthly Azure cost: ${run.total_monthly_cost_usd:,.4f}")
        lines.append(f"  Cost per user:            ${run.cost_per_user_usd:,.6f}")
        if run.expected_cost_range:
            ec = run.expected_cost_range
            status = "OK" if ec.in_range else "WARN (out of range)"
            lines.append(
                f"  Expected cost range:      {ec.range_label}/mo  "
                f"(actual ${ec.actual_usd:,.2f}) [{status}]"
            )
            if ec.rationale:
                lines.append(f"  Range rationale:          {ec.rationale}")
        lines.append(f"  Largest cost drivers:")
        for driver in run.largest_cost_drivers:
            lines.append(f"    - {driver}")
        lines.append(f"  Pricing completeness:     {run.pricing_completeness}")
        if run.warnings:
            lines.append(f"  Warnings:")
            for warning in run.warnings:
                lines.append(f"    - {warning}")
        if run.missing_prices:
            lines.append(f"  Missing prices:")
            for item in run.missing_prices:
                lines.append(f"    - {item}")

        lines.append("")
        lines.append("VALIDATION CHECKS")
        lines.append("-" * 100)
        for check in run.validation_checks:
            icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(check.status.value, "?")
            lines.append(f"  [{icon}] {check.rule_name}: {check.message}")
            for detail in check.details[:5]:
                lines.append(f"      - {detail}")
        lines.append("")
        return "\n".join(lines)

    def format_assessment(self, assessment: ScenarioAssessment) -> str:
        lines: list[str] = []
        lines.append("=" * 100)
        lines.append(f"SCENARIO ASSESSMENT: {assessment.scenario_name}")
        lines.append("=" * 100)
        realistic = "Yes" if assessment.looks_realistic else "No (review needed)"
        lines.append(f"  Automated realism check: {realistic}")
        lines.append(f"  Notes: {assessment.realism_notes}")
        lines.append(
            f"  Validation: {assessment.validation_pass_count} pass, "
            f"{assessment.validation_warn_count} warn, "
            f"{assessment.validation_fail_count} fail"
        )
        lines.append("")
        lines.append("  Pipeline category scores (1-10):")
        scores = assessment.category_scores
        lines.append(f"    Usage Assumptions:          {scores.usage_assumptions}/10")
        lines.append(f"    Azure Service Selection:    {scores.azure_service_selection}/10")
        lines.append(f"    SKU Quantity Calculation:   {scores.sku_quantity_calculation}/10")
        lines.append(f"    Free Tier / Included Usage: {scores.free_tier_included_usage}/10")
        lines.append(f"    Catalog Price Mapping:      {scores.catalog_price_mapping}/10")
        lines.append(f"    Overall:                    {scores.overall}/10")

        if assessment.expected_cost_results:
            lines.append("")
            lines.append("  Expected cost range vs actual:")
            header = f"    {'Users':<10} {'Expected Range':<20} {'Actual':<12} Status"
            lines.append(header)
            for result in assessment.expected_cost_results:
                status = "OK" if result.in_range else "WARN"
                users_text = f"{result.users:,}"
                lines.append(
                    f"    {users_text:<10} {result.range_label:<20} "
                    f"${result.actual_usd:>9,.2f}  {status}"
                )
        lines.append("")
        lines.append("  HUMAN VALIDATION (engineering review)")
        lines.append("-" * 100)
        human = assessment.human_validation
        lines.append(
            f"  Does this estimate look realistic? "
            f"{'Yes' if human.looks_realistic else 'No — review needed'}"
        )
        lines.append(f"  Why? {human.realism_explanation}")
        lines.append("")
        lines.append("  Largest cost drivers:")
        for item in human.largest_cost_drivers:
            lines.append(f"    - {item}")
        lines.append("")
        lines.append("  Assumptions with greatest impact:")
        for item in human.highest_impact_assumptions:
            lines.append(f"    - {item}")
        lines.append("")
        lines.append("  Assumptions that should probably be refined:")
        for item in human.assumptions_to_refine:
            lines.append(f"    - {item}")
        lines.append("")
        lines.append(f"  Review summary: {human.review_summary}")
        lines.append("")
        lines.append("  Recommended next improvements:")
        for item in assessment.recommended_improvements:
            lines.append(f"    - {item}")
        lines.append("")
        return "\n".join(lines)

    def format_suite_summary(self, report: AzurePricingValidationSuiteReport) -> str:
        lines: list[str] = []
        lines.append("=" * 100)
        lines.append("AZURE PRICING VALIDATION SUITE — SUMMARY")
        lines.append("=" * 100)
        lines.append(f"Inference mode: {report.inference_mode}")
        lines.append(f"Scenarios: {len(report.scenario_assessments)}")
        lines.append(f"Total runs: {len(report.scenario_runs)}")
        lines.append("")

        lines.append("Cost summary by scenario:")
        lines.append("-" * 100)
        header = f"{'Scenario':<35} {'100':>12} {'1,000':>12} {'10,000':>12} {'100,000':>12}"
        lines.append(header)
        lines.append("-" * len(header))
        scenario_ids = []
        for run in report.scenario_runs:
            if run.scenario_id not in scenario_ids:
                scenario_ids.append(run.scenario_id)
        for scenario_id in scenario_ids:
            runs = [r for r in report.scenario_runs if r.scenario_id == scenario_id]
            name = runs[0].scenario_name if runs else scenario_id
            costs = []
            for user_count in BENCHMARK_USER_COUNTS:
                match = next((r for r in runs if r.users == user_count), None)
                if match is None:
                    costs.append("N/A")
                else:
                    costs.append(f"${match.total_monthly_cost_usd:,.2f}")
            lines.append(f"{name:<35} {costs[0]:>12} {costs[1]:>12} {costs[2]:>12} {costs[3]:>12}")

        lines.append("")
        lines.append("Expected cost range validation:")
        lines.append("-" * 100)
        range_header = (
            f"{'Scenario':<28} {'Users':>8} {'Expected Range':<18} "
            f"{'Actual':>12} {'Status':>6}"
        )
        lines.append(range_header)
        lines.append("-" * len(range_header))
        for scenario_id in scenario_ids:
            runs = [r for r in report.scenario_runs if r.scenario_id == scenario_id]
            short_name = runs[0].scenario_name[:28] if runs else scenario_id[:28]
            for run in runs:
                if run.expected_cost_range is None:
                    continue
                ec = run.expected_cost_range
                status = "OK" if ec.in_range else "WARN"
                users_label = f"{run.users:,}"
                if run.users >= 100_000:
                    users_label = "100K"
                elif run.users >= 10_000:
                    users_label = "10K"
                elif run.users >= 1_000:
                    users_label = "1K"
                lines.append(
                    f"{short_name:<28} {users_label:>8} {ec.range_label:<18} "
                    f"${ec.actual_usd:>10,.2f} {status:>6}"
                )

        lines.append("")
        for check in report.suite_validation_summary:
            icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(check.status.value, "?")
            lines.append(f"[{icon}] {check.rule_name}: {check.message}")
        lines.append("")
        return "\n".join(lines)

    def format_full(self, report: AzurePricingValidationSuiteReport) -> str:
        parts = [self.format_suite_summary(report)]
        for run in report.scenario_runs:
            parts.append(self.format_run(run))
        for assessment in report.scenario_assessments:
            parts.append(self.format_assessment(assessment))
        return "\n".join(parts)

    def format_json(self, report: AzurePricingValidationSuiteReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2)

    @staticmethod
    def _format_assumption_line(item: UsageAssumptionDetail) -> str:
        parts = [f"    {item.key}={_fmt_scalar(item.value)}"]
        if item.unit:
            parts[0] += f" {item.unit}"
        meta: list[str] = []
        if item.confidence:
            meta.append(f"confidence={item.confidence}")
        if item.source:
            meta.append(f"source={item.source}")
        if meta:
            parts.append(f" ({', '.join(meta)})")
        line = "".join(parts)
        if item.reasoning:
            line += f"\n      reasoning: {item.reasoning}"
        return line
