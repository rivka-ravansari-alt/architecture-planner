"""Azure component pricing benchmark for a fixed product scenario."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.azure.usage_inference import InferenceMode
from app.pricing.azure.verification import (
    AzurePricingVerificationRunner,
    ComponentVerificationReport,
    SkuVerificationLine,
)
from app.pricing.azure.scenarios import (
    SELF_ESTEEM_HABIT,
    scenario_components,
    self_esteem_scenario_definition,
)
from app.schemas.domain import MappedComponent


class ComponentRole(str, Enum):
    BACKEND_API = "backend_api"
    DATABASE = "database"
    STORAGE = "storage"
    QUEUE_BACKGROUND = "queue_background"


SELF_ESTEEM_PRODUCT_DESCRIPTION = SELF_ESTEEM_HABIT.product_description

BENCHMARK_USER_COUNTS: tuple[int, ...] = (100, 1_000, 10_000, 100_000)

# Maps benchmark user count to Project.expected_users labels used by usage inference.
USER_COUNT_TO_PROJECT_LABEL: dict[int, str] = {
    100: "100",
    1_000: "1000",
    10_000: "10000",
    100_000: "100000+",
}

COMPONENT_ROLE_BY_ID: dict[str, ComponentRole] = {
    "api": ComponentRole.BACKEND_API,
    "database": ComponentRole.DATABASE,
    "files": ComponentRole.STORAGE,
    "notifications": ComponentRole.QUEUE_BACKGROUND,
}

ROLE_DISPLAY_NAME: dict[ComponentRole, str] = {
    ComponentRole.BACKEND_API: "Backend/API",
    ComponentRole.DATABASE: "Database",
    ComponentRole.STORAGE: "Storage",
    ComponentRole.QUEUE_BACKGROUND: "Queue/Background",
}


class ComponentBenchmarkRow(BaseModel):
    """One Azure component row for a single user-count scenario."""

    users: int
    component: str
    component_role: ComponentRole
    azure_service: str
    usage_assumptions: str
    raw_sku_quantities: str
    free_tier_deducted: str
    billable_quantities: str
    unit_prices: str
    component_monthly_cost: float
    warnings_missing: str
    has_unpriced_billable_usage: bool = False
    silent_zero_due_to_missing_price: bool = False


class UserCountSummaryRow(BaseModel):
    """Summary row for one user-count scenario."""

    users: int
    backend_api_cost: float
    database_cost: float
    storage_cost: float
    queue_background_cost: float
    total_azure_monthly_cost: float
    pricing_completeness: str
    main_reason_for_cost_increase: str
    missing_price_count: int = 0
    unpriced_billable_sku_count: int = 0


class AzureComponentPricingBenchmarkReport(BaseModel):
    """Full benchmark output across all user counts."""

    scenario_name: str = "Self-Esteem App"
    scenario_description: str = SELF_ESTEEM_PRODUCT_DESCRIPTION
    user_counts: list[int] = Field(default_factory=lambda: list(BENCHMARK_USER_COUNTS))
    component_rows: list[ComponentBenchmarkRow] = Field(default_factory=list)
    summary_rows: list[UserCountSummaryRow] = Field(default_factory=list)


@dataclass(frozen=True)
class _ScenarioDefinition:
    project_name: str
    stage: str
    feature_flags: dict[str, bool]
    components: list[MappedComponent]


def self_esteem_scenario() -> _ScenarioDefinition:
    """Architecture for the self-esteem product benchmark."""
    scenario = self_esteem_scenario_definition()
    return _ScenarioDefinition(
        project_name=scenario.name,
        stage=scenario.stage,
        feature_flags=dict(scenario.feature_flags),
        components=scenario_components(scenario),
    )


class AzureComponentPricingBenchmark:
    """Run the self-esteem scenario across benchmark user counts."""

    def __init__(self, verification_runner: AzurePricingVerificationRunner) -> None:
        self._runner = verification_runner
        self._scenario = self_esteem_scenario()

    def run(
        self,
        *,
        inference_mode: InferenceMode = "heuristic",
    ) -> AzureComponentPricingBenchmarkReport:
        component_rows: list[ComponentBenchmarkRow] = []
        summary_rows: list[UserCountSummaryRow] = []
        previous_summary: UserCountSummaryRow | None = None

        for users in BENCHMARK_USER_COUNTS:
            project = Project(
                name=self._scenario.project_name,
                description=SELF_ESTEEM_PRODUCT_DESCRIPTION,
                expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
                stage=self._scenario.stage,
            )
            verification = self._runner.run(
                project,
                self._scenario.components,
                feature_flags=self._scenario.feature_flags,
                inference_mode=inference_mode,
            )
            rows = [
                _component_row_from_verification(users, component)
                for component in verification.components
            ]
            component_rows.extend(rows)
            summary = _summary_from_rows(users, rows, previous_summary)
            summary_rows.append(summary)
            previous_summary = summary

        return AzureComponentPricingBenchmarkReport(
            component_rows=component_rows,
            summary_rows=summary_rows,
        )


def _component_row_from_verification(
    users: int,
    component: ComponentVerificationReport,
) -> ComponentBenchmarkRow:
    role = COMPONENT_ROLE_BY_ID.get(
        component.architecture.component_id,
        ComponentRole.BACKEND_API,
    )
    unpriced_billable = _count_unpriced_billable_skus(component.sku_lines)
    silent_zero = _has_silent_zero(component, unpriced_billable)

    warnings_parts: list[str] = []
    for line in component.sku_lines:
        if line.billable_quantity <= 0 or line.sku_cost_usd is not None:
            continue
        if line.missing_price_reason:
            warnings_parts.append(
                f"MISSING PRICE: {line.sku_key} ({line.catalog_role}): {line.missing_price_reason}"
            )
        else:
            warnings_parts.append(
                f"UNPRICED BILLABLE: {line.sku_key} has billable quantity "
                f"{_fmt_scalar(line.billable_quantity)} but no priced line item."
            )
    for warning in _dedupe_preserve_order(component.warnings):
        if warning not in warnings_parts:
            warnings_parts.append(warning)
    if unpriced_billable:
        warnings_parts.append(
            f"UNPRICED BILLABLE USAGE: {unpriced_billable} SKU(s) have billable quantity "
            "but no catalog unit price."
        )
    if silent_zero:
        warnings_parts.append(
            "SILENT ZERO: component monthly cost is $0.00 while billable usage exists "
            "without catalog prices."
        )

    return ComponentBenchmarkRow(
        users=users,
        component=component.architecture.component_name,
        component_role=role,
        azure_service=component.azure_service,
        usage_assumptions=_format_assumptions(component.usage_assumptions),
        raw_sku_quantities=_format_quantities(component.raw_sku_quantities, use_raw=True),
        free_tier_deducted=_format_deductions(component),
        billable_quantities=_format_quantities(component.billable_sku_quantities, use_raw=False),
        unit_prices=_format_unit_prices(component.sku_lines),
        component_monthly_cost=round(component.subtotal_usd, 4),
        warnings_missing=" | ".join(warnings_parts) if warnings_parts else "-",
        has_unpriced_billable_usage=unpriced_billable > 0,
        silent_zero_due_to_missing_price=silent_zero,
    )


def _summary_from_rows(
    users: int,
    rows: list[ComponentBenchmarkRow],
    previous: UserCountSummaryRow | None,
) -> UserCountSummaryRow:
    costs = {role: 0.0 for role in ComponentRole}
    missing_count = 0
    unpriced_count = 0
    for row in rows:
        costs[row.component_role] += row.component_monthly_cost
        missing_count += row.warnings_missing.count("MISSING PRICE:")
        missing_count += row.warnings_missing.count("UNPRICED BILLABLE:")
        if row.has_unpriced_billable_usage:
            unpriced_count += 1

    total = sum(costs.values())
    completeness = "complete" if missing_count == 0 and unpriced_count == 0 else "incomplete"

    return UserCountSummaryRow(
        users=users,
        backend_api_cost=round(costs[ComponentRole.BACKEND_API], 4),
        database_cost=round(costs[ComponentRole.DATABASE], 4),
        storage_cost=round(costs[ComponentRole.STORAGE], 4),
        queue_background_cost=round(costs[ComponentRole.QUEUE_BACKGROUND], 4),
        total_azure_monthly_cost=round(total, 4),
        pricing_completeness=completeness,
        main_reason_for_cost_increase=_main_cost_increase_reason(rows, previous, total),
        missing_price_count=missing_count,
        unpriced_billable_sku_count=unpriced_count,
    )


def _main_cost_increase_reason(
    rows: list[ComponentBenchmarkRow],
    previous: UserCountSummaryRow | None,
    total: float,
) -> str:
    if previous is None:
        return "Baseline: SQL S1 instance and namespace/storage minimums dominate at low scale."

    deltas = {
        ComponentRole.BACKEND_API: sum(
            row.component_monthly_cost
            for row in rows
            if row.component_role == ComponentRole.BACKEND_API
        )
        - previous.backend_api_cost,
        ComponentRole.DATABASE: sum(
            row.component_monthly_cost
            for row in rows
            if row.component_role == ComponentRole.DATABASE
        )
        - previous.database_cost,
        ComponentRole.STORAGE: sum(
            row.component_monthly_cost
            for row in rows
            if row.component_role == ComponentRole.STORAGE
        )
        - previous.storage_cost,
        ComponentRole.QUEUE_BACKGROUND: sum(
            row.component_monthly_cost
            for row in rows
            if row.component_role == ComponentRole.QUEUE_BACKGROUND
        )
        - previous.queue_background_cost,
    }
    total_delta = total - previous.total_azure_monthly_cost
    if abs(total_delta) < 0.01:
        return "Total flat: fixed-tier services (SQL instance) dominate over usage growth."

    top_role = max(deltas, key=lambda role: deltas[role])
    top_delta = deltas[top_role]
    if top_delta <= 0.01:
        secondary = max(deltas.values())
        if secondary <= 0.01:
            return "Total flat: fixed-tier services (SQL instance) dominate over usage growth."
        top_role = max(deltas, key=lambda role: deltas[role])

    return (
        f"{ROLE_DISPLAY_NAME[top_role]} scales with users "
        f"(+${top_delta:,.2f} vs {previous.users:,} users; total +${total_delta:,.2f})."
    )


def _count_unpriced_billable_skus(lines: Iterable[SkuVerificationLine]) -> int:
    return sum(
        1
        for line in lines
        if line.billable_quantity > 0 and line.sku_cost_usd is None
    )


def _has_silent_zero(component: ComponentVerificationReport, unpriced_billable: int) -> bool:
    has_billable = any(line.billable_quantity > 0 for line in component.sku_lines)
    return (
        has_billable
        and component.subtotal_usd == 0
        and unpriced_billable > 0
    )


def _format_assumptions(assumptions: dict[str, int | float | str | bool]) -> str:
    if not assumptions:
        return "-"
    return "; ".join(f"{key}={_fmt_scalar(value)}" for key, value in sorted(assumptions.items()))


def _format_quantities(quantities, *, use_raw: bool) -> str:
    if not quantities:
        return "-"
    parts: list[str] = []
    for item in quantities:
        qty = item.raw_quantity if use_raw and item.raw_quantity is not None else item.quantity
        parts.append(f"{item.sku_key}={_fmt_scalar(qty)} {item.unit}")
    return "; ".join(parts)


def _format_deductions(component: ComponentVerificationReport) -> str:
    parts: list[str] = []
    for item in component.included_usage:
        parts.append(
            f"{item['sku_key']}: tier/plan included {_fmt_scalar(item['quantity'])} {item['unit']}"
        )
    for line in component.sku_lines:
        deductions: list[str] = []
        if line.tier_included_quantity > 0:
            deductions.append(f"tier_included={_fmt_scalar(line.tier_included_quantity)}")
        if line.free_tier_deducted > 0:
            deductions.append(f"free_tier={_fmt_scalar(line.free_tier_deducted)}")
        if deductions:
            parts.append(f"{line.sku_key}: {', '.join(deductions)}")
    return "; ".join(parts) if parts else "-"


def _format_unit_prices(lines: Iterable[SkuVerificationLine]) -> str:
    parts: list[str] = []
    for line in lines:
        if line.unit_price_usd is not None:
            parts.append(
                f"{line.sku_key}: ${line.unit_price_usd} per {line.catalog_usage_unit}"
            )
        elif line.billable_quantity > 0:
            if line.missing_price_reason:
                parts.append(f"{line.sku_key}: MISSING ({line.missing_price_reason})")
            else:
                parts.append(f"{line.sku_key}: UNPRICED (billable, no catalog line)")
    return "; ".join(parts) if parts else "-"


def _fmt_scalar(value: int | float | str | bool) -> str:
    if isinstance(value, float):
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text
    if isinstance(value, int) and abs(value) >= 1000:
        return f"{value:,}"
    return str(value)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


class AzureComponentPricingBenchmarkFormatter:
    """Render benchmark results as readable tables."""

    COMPONENT_HEADERS = [
        "users",
        "component",
        "Azure service",
        "usage assumptions used",
        "raw SKU quantities",
        "free tier / included usage deducted",
        "billable quantities",
        "unit prices from catalog",
        "component monthly cost",
        "warnings / missing prices",
    ]

    SUMMARY_HEADERS = [
        "users",
        "Backend/API cost",
        "Database cost",
        "Storage cost",
        "Queue/Background cost",
        "Total Azure monthly cost",
        "Pricing completeness",
        "Main reason for cost increase",
    ]

    def format(self, report: AzureComponentPricingBenchmarkReport) -> str:
        lines: list[str] = []
        lines.append("=" * 120)
        lines.append("AZURE COMPONENT PRICING BENCHMARK")
        lines.append("=" * 120)
        lines.append(f"Scenario: {report.scenario_name}")
        lines.append(f"Description: {report.scenario_description}")
        lines.append("")

        for users in report.user_counts:
            rows = [row for row in report.component_rows if row.users == users]
            lines.append("-" * 120)
            lines.append(f"USER COUNT: {users:,}")
            lines.append("-" * 120)
            lines.append(_render_table(self.COMPONENT_HEADERS, [_component_table_row(row) for row in rows]))
            lines.append("")

        lines.append("=" * 120)
        lines.append("SUMMARY")
        lines.append("=" * 120)
        lines.append(
            _render_table(
                self.SUMMARY_HEADERS,
                [_summary_table_row(row) for row in report.summary_rows],
            )
        )
        lines.append("")
        return "\n".join(lines)

    def format_json(self, report: AzureComponentPricingBenchmarkReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2)


def _component_table_row(row: ComponentBenchmarkRow) -> list[str]:
    return [
        str(row.users),
        row.component,
        row.azure_service,
        row.usage_assumptions,
        row.raw_sku_quantities,
        row.free_tier_deducted,
        row.billable_quantities,
        row.unit_prices,
        f"${row.component_monthly_cost:,.4f}",
        row.warnings_missing,
    ]


def _summary_table_row(row: UserCountSummaryRow) -> list[str]:
    return [
        str(row.users),
        f"${row.backend_api_cost:,.4f}",
        f"${row.database_cost:,.4f}",
        f"${row.storage_cost:,.4f}",
        f"${row.queue_background_cost:,.4f}",
        f"${row.total_azure_monthly_cost:,.4f}",
        row.pricing_completeness,
        row.main_reason_for_cost_increase,
    ]


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "(no rows)"

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    divider = "-+-".join("-" * width for width in widths)
    lines = [fmt_row(headers), divider]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)
