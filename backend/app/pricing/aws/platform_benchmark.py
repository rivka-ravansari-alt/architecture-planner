"""AWS platform scenario benchmark with random user counts per scenario."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.aws.benchmark import (
    AwsScenarioPricingBenchmarkFormatter,
    ComponentBenchmarkDetail,
    UserCountRunRow,
    build_usage_service,
    normalize_aws_components,
)
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.scenarios import AWS_PLATFORM_BENCHMARK_SCENARIOS, platform_scenario_components
from app.pricing.azure.scenarios import BenchmarkScenario
from app.pricing.usage.service import UsageAssumptionsService
from app.schemas.domain import MappedComponent

InferenceMode = Literal["llm", "heuristic"]

# Expanded pool for randomized monthly-active-user assignment per scenario.
PLATFORM_RANDOM_USER_POOL: tuple[int, ...] = (
    150,
    420,
    850,
    1_800,
    3_500,
    7_200,
    12_500,
    28_000,
    55_000,
    95_000,
)


def user_count_to_project_label(users: int) -> str:
    """Map an arbitrary MAU to the nearest Project.expected_users band label."""
    if users <= 100:
        return "100"
    if users <= 1_000:
        return "1000"
    if users <= 10_000:
        return "10000"
    return "100000+"


def assign_random_user_counts(
    scenario_count: int,
    *,
    pool: tuple[int, ...] = PLATFORM_RANDOM_USER_POOL,
    seed: int | None = None,
) -> list[int]:
    """Pick one random user count per scenario (unique when pool is large enough)."""
    rng = random.Random(seed)
    if scenario_count <= len(pool):
        return rng.sample(list(pool), k=scenario_count)
    return [rng.choice(pool) for _ in range(scenario_count)]


class PlatformScenarioRunRow(UserCountRunRow):
    """One scenario run with assigned random users and per-component pricing status."""

    assigned_users: int
    supported_component_count: int = 0
    unsupported_component_count: int = 0
    component_services: list[str] = Field(default_factory=list)
    pricing_status_by_component: dict[str, str] = Field(default_factory=dict)


class PlatformScenarioReport(BaseModel):
    scenario_id: str
    name: str
    product_description: str
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    architecture_components: list[dict[str, str]] = Field(default_factory=list)
    assigned_users: int
    row: PlatformScenarioRunRow


class AwsPlatformScenarioBenchmarkReport(BaseModel):
    provider: str = "aws"
    inference_mode: InferenceMode
    random_seed: int | None = None
    user_assignments: list[int] = Field(default_factory=list)
    scenarios: list[PlatformScenarioReport] = Field(default_factory=list)


@dataclass
class AwsPlatformScenarioBenchmark:
    """Run AWS catalog pricing for platform scenarios with one random MAU each."""

    pipeline: AwsProjectCostingPipeline
    usage_service: UsageAssumptionsService
    inference_mode: InferenceMode = "heuristic"
    scenarios: tuple[BenchmarkScenario, ...] = AWS_PLATFORM_BENCHMARK_SCENARIOS
    random_seed: int | None = 42

    def run(self) -> AwsPlatformScenarioBenchmarkReport:
        user_assignments = assign_random_user_counts(
            len(self.scenarios),
            seed=self.random_seed,
        )
        scenario_reports: list[PlatformScenarioReport] = []
        for scenario, assigned_users in zip(self.scenarios, user_assignments, strict=True):
            components = normalize_aws_components(platform_scenario_components(scenario))
            row = self._run_scenario(scenario, components, assigned_users)
            from app.pricing.aws.benchmark import scenario_component_summary

            scenario_reports.append(
                PlatformScenarioReport(
                    scenario_id=scenario.scenario_id,
                    name=scenario.name,
                    product_description=scenario.product_description,
                    feature_flags=dict(scenario.feature_flags),
                    architecture_components=scenario_component_summary(scenario),
                    assigned_users=assigned_users,
                    row=row,
                )
            )
        return AwsPlatformScenarioBenchmarkReport(
            inference_mode=self.inference_mode,
            random_seed=self.random_seed,
            user_assignments=user_assignments,
            scenarios=scenario_reports,
        )

    def _run_scenario(
        self,
        scenario: BenchmarkScenario,
        components: list[MappedComponent],
        assigned_users: int,
    ) -> PlatformScenarioRunRow:
        project = Project(
            name=scenario.name,
            description=scenario.product_description,
            expected_users=user_count_to_project_label(assigned_users),
            stage=scenario.stage,
        )
        inference = self.usage_service.infer(
            project,
            components,
            provider="aws",
            feature_flags=scenario.feature_flags,
            inference_mode=self.inference_mode,
        )
        pricing_inputs = list(inference.components)
        result = self.pipeline.calculate(
            project,
            components,
            pricing_inputs=pricing_inputs,
            feature_flags=scenario.feature_flags,
        )
        component_details = self._component_details(pricing_inputs, result.components)
        status_by_component = {
            item.component_id: item.pricing_status for item in result.components
        }
        return PlatformScenarioRunRow(
            users=assigned_users,
            assigned_users=assigned_users,
            total_usd=round(result.total_usd, 2),
            inference_source=inference.inference_source,
            components=component_details,
            warnings=list(result.warnings),
            supported_component_count=result.supported_component_count,
            unsupported_component_count=result.unsupported_component_count,
            component_services=[item.cloud_service for item in pricing_inputs],
            pricing_status_by_component=status_by_component,
        )

    @staticmethod
    def _component_details(pricing_inputs, cost_components) -> list[ComponentBenchmarkDetail]:
        from app.pricing.aws.benchmark import AwsScenarioPricingBenchmark

        return AwsScenarioPricingBenchmark._component_details(pricing_inputs, cost_components)


class AwsPlatformScenarioBenchmarkFormatter:
    """Text formatter for platform scenario benchmark reports."""

    @staticmethod
    def format_summary_table(report: AwsPlatformScenarioBenchmarkReport) -> str:
        lines = [
            "AWS PLATFORM SCENARIO BENCHMARK (monthly USD, random MAU per scenario)",
            f"Inference mode: {report.inference_mode}",
            f"Random seed: {report.random_seed}",
            "",
            f"{'Scenario':<32} {'Users':>10} {'Total USD':>14} {'Supported':>10}",
            "-" * 70,
        ]
        for scenario in report.scenarios:
            row = scenario.row
            lines.append(
                f"{scenario.name[:32]:<32} {row.assigned_users:>10,} "
                f"${row.total_usd:>13,.2f} {row.supported_component_count:>10}"
            )
        return "\n".join(lines)

    @staticmethod
    def format_component_breakdown(report: AwsPlatformScenarioBenchmarkReport) -> str:
        lines: list[str] = ["COMPONENT BREAKDOWN BY SCENARIO", ""]
        for scenario in report.scenarios:
            lines.append(f"## {scenario.name} ({scenario.scenario_id}) — {scenario.assigned_users:,} users")
            for comp in scenario.row.components:
                status = scenario.row.pricing_status_by_component.get(comp.component_id, "?")
                lines.append(
                    f"  {comp.component_id:<18} {comp.aws_service:<22} "
                    f"${comp.subtotal_usd:>9,.2f}  [{status}]"
                )
            lines.append(f"  {'TOTAL':<18} {'':<22} ${scenario.row.total_usd:>9,.2f}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def format_service_price_table(report: AwsPlatformScenarioBenchmarkReport) -> str:
        """Table: App Name | Users | Service | Price (USD) — one row per component."""
        headers = ("App Name", "Users", "Service", "Price (USD)")
        rows: list[tuple[str, str, str, str]] = []
        for scenario in report.scenarios:
            app_name = scenario.name
            users = f"{scenario.assigned_users:,}"
            for comp in scenario.row.components:
                rows.append(
                    (
                        app_name,
                        users,
                        comp.aws_service,
                        f"{comp.subtotal_usd:,.2f}",
                    )
                )
            rows.append((app_name, users, "TOTAL", f"{scenario.row.total_usd:,.2f}"))

        col_widths = [
            max(len(headers[i]), *(len(row[i]) for row in rows), 10 if i == 1 else 0)
            for i in range(len(headers))
        ]
        col_widths[0] = max(col_widths[0], 28)

        def _fmt_row(cells: tuple[str, ...]) -> str:
            return (
                f"{cells[0]:<{col_widths[0]}}  "
                f"{cells[1]:>{col_widths[1]}}  "
                f"{cells[2]:<{col_widths[2]}}  "
                f"{cells[3]:>{col_widths[3]}}"
            )

        lines = [
            "SERVICE PRICING BY APP (monthly USD)",
            _fmt_row(headers),
            _fmt_row(tuple("-" * w for w in col_widths)),
        ]
        lines.extend(_fmt_row(row) for row in rows)
        return "\n".join(lines)

    @classmethod
    def format_full_report(cls, report: AwsPlatformScenarioBenchmarkReport) -> str:
        from app.pricing.aws.benchmark import AwsScenarioPricingBenchmarkFormatter

        legacy = cls._legacy_adapter(report)
        sections = [
            cls.format_service_price_table(report),
            "",
            cls.format_summary_table(report),
            "",
            cls.format_component_breakdown(report),
            "",
            AwsScenarioPricingBenchmarkFormatter.format_scenario_components(legacy),
        ]
        return "\n".join(sections)

    @staticmethod
    def _legacy_adapter(report: AwsPlatformScenarioBenchmarkReport):
        from app.pricing.aws.benchmark import AwsScenarioPricingBenchmarkReport, ScenarioBenchmarkReport

        return AwsScenarioPricingBenchmarkReport(
            inference_mode=report.inference_mode,
            user_counts=report.user_assignments,
            scenarios=[
                ScenarioBenchmarkReport(
                    scenario_id=s.scenario_id,
                    name=s.name,
                    product_description=s.product_description,
                    feature_flags=s.feature_flags,
                    architecture_components=s.architecture_components,
                    rows=[s.row],
                )
                for s in report.scenarios
            ],
        )

    @staticmethod
    def to_serializable(report: AwsPlatformScenarioBenchmarkReport) -> dict:
        return report.model_dump()
