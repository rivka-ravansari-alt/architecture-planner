"""AWS catalog pricing benchmark across benchmark scenarios and user counts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.clients.ai_client import BaseAIClient
from app.models import Project
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS, USER_COUNT_TO_PROJECT_LABEL
from app.pricing.azure.scenarios import (
    AI_CHAT,
    AI_DOCUMENT_OCR,
    ECOMMERCE,
    SELF_ESTEEM_HABIT,
    SIMPLE_CRUD_SAAS,
    BenchmarkScenario,
    scenario_components,
)
from app.pricing.usage.service import UsageAssumptionsService
from app.schemas.domain import MappedComponent

InferenceMode = Literal["llm", "heuristic"]

# Five representative benchmark scenarios for AWS MVP pricing (Lambda, RDS, S3, SQS).
AWS_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    SIMPLE_CRUD_SAAS,
    SELF_ESTEEM_HABIT,
    ECOMMERCE,
    AI_CHAT,
    AI_DOCUMENT_OCR,
)

_AWS_SERVICE_ALIASES = {
    "rds postgresql": "RDS",
    "rds mysql": "RDS",
}


def normalize_aws_components(components: list[MappedComponent]) -> list[MappedComponent]:
    """Map catalog display names to AwsPricingModelRegistry keys."""
    normalized: list[MappedComponent] = []
    for component in components:
        item = deepcopy(component)
        aws_name = str(item.cloud.get("aws", ""))
        alias = _AWS_SERVICE_ALIASES.get(aws_name.strip().casefold())
        if alias:
            item.cloud = dict(item.cloud)
            item.cloud["aws"] = alias
        normalized.append(item)
    return normalized


def scenario_component_summary(scenario: BenchmarkScenario) -> list[dict[str, str]]:
    """Return component metadata for reporting."""
    return [
        {
            "component_id": spec.key,
            "name": spec.name,
            "component_type": spec.component_type,
            "aws_service": spec.aws_service,
            "azure_service": spec.azure_service,
        }
        for spec in scenario.components
    ]


class UsageAssumptionDetail(BaseModel):
    key: str
    value: float | int | str
    unit: str = ""
    confidence: str = ""
    reasoning: str = ""


class ComponentBenchmarkDetail(BaseModel):
    component_id: str
    aws_service: str
    subtotal_usd: float
    behavioral_assumptions: list[UsageAssumptionDetail] = Field(default_factory=list)
    resolved_assumptions: list[UsageAssumptionDetail] = Field(default_factory=list)


class UserCountRunRow(BaseModel):
    users: int
    total_usd: float
    inference_source: str
    components: list[ComponentBenchmarkDetail] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScenarioBenchmarkReport(BaseModel):
    scenario_id: str
    name: str
    product_description: str
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    architecture_components: list[dict[str, str]] = Field(default_factory=list)
    rows: list[UserCountRunRow] = Field(default_factory=list)


class AwsScenarioPricingBenchmarkReport(BaseModel):
    provider: str = "aws"
    inference_mode: InferenceMode
    user_counts: list[int] = Field(default_factory=lambda: list(BENCHMARK_USER_COUNTS))
    scenarios: list[ScenarioBenchmarkReport] = Field(default_factory=list)


@dataclass
class AwsScenarioPricingBenchmark:
    """Run AWS catalog pricing for benchmark scenarios with usage inference."""

    pipeline: AwsProjectCostingPipeline
    usage_service: UsageAssumptionsService
    inference_mode: InferenceMode = "llm"
    scenarios: tuple[BenchmarkScenario, ...] = AWS_BENCHMARK_SCENARIOS
    user_counts: tuple[int, ...] = BENCHMARK_USER_COUNTS

    def run(self) -> AwsScenarioPricingBenchmarkReport:
        scenario_reports: list[ScenarioBenchmarkReport] = []
        for scenario in self.scenarios:
            components = normalize_aws_components(scenario_components(scenario))
            rows: list[UserCountRunRow] = []
            for users in self.user_counts:
                rows.append(
                    self._run_user_count(
                        scenario,
                        components,
                        users,
                    )
                )
            scenario_reports.append(
                ScenarioBenchmarkReport(
                    scenario_id=scenario.scenario_id,
                    name=scenario.name,
                    product_description=scenario.product_description,
                    feature_flags=dict(scenario.feature_flags),
                    architecture_components=scenario_component_summary(scenario),
                    rows=rows,
                )
            )
        return AwsScenarioPricingBenchmarkReport(
            inference_mode=self.inference_mode,
            scenarios=scenario_reports,
        )

    def _run_user_count(
        self,
        scenario: BenchmarkScenario,
        components: list[MappedComponent],
        users: int,
    ) -> UserCountRunRow:
        project = Project(
            name=scenario.name,
            description=scenario.product_description,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
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
        return UserCountRunRow(
            users=users,
            total_usd=round(result.total_usd, 2),
            inference_source=inference.inference_source,
            components=component_details,
            warnings=list(result.warnings),
        )

    @staticmethod
    def _component_details(pricing_inputs, cost_components) -> list[ComponentBenchmarkDetail]:
        details: list[ComponentBenchmarkDetail] = []
        for component_input in pricing_inputs:
            cost_component = next(
                (c for c in cost_components if c.component_id == component_input.component_id),
                None,
            )

            def _serialize(assumptions) -> list[UsageAssumptionDetail]:
                return [
                    UsageAssumptionDetail(
                        key=a.key,
                        value=a.value,
                        unit=a.unit or "",
                        confidence=str(getattr(a.confidence, "value", a.confidence)),
                        reasoning=a.reasoning or "",
                    )
                    for a in assumptions
                ]

            details.append(
                ComponentBenchmarkDetail(
                    component_id=component_input.component_id,
                    aws_service=component_input.cloud_service,
                    subtotal_usd=round(cost_component.subtotal_usd, 2) if cost_component else 0.0,
                    behavioral_assumptions=_serialize(component_input.behavioral_assumptions),
                    resolved_assumptions=_serialize(component_input.resolved),
                )
            )
        return details


def build_usage_service(
    *,
    ai_client: BaseAIClient | None = None,
    inference_mode: InferenceMode = "llm",
) -> UsageAssumptionsService:
    if inference_mode == "heuristic":
        return UsageAssumptionsService(inference_mode="heuristic")
    return UsageAssumptionsService(ai_client=ai_client, inference_mode="llm")


class AwsScenarioPricingBenchmarkFormatter:
    """Text formatter for AWS scenario benchmark reports."""

    @staticmethod
    def format_summary_table(report: AwsScenarioPricingBenchmarkReport) -> str:
        lines = [
            "AWS SCENARIO PRICING BENCHMARK (monthly USD)",
            f"Inference mode: {report.inference_mode}",
            "",
        ]
        header = f"{'Scenario':<28}" + "".join(f"{u:>12,}" for u in report.user_counts)
        lines.append(header)
        lines.append("-" * len(header))
        for scenario in report.scenarios:
            totals = {row.users: row.total_usd for row in scenario.rows}
            row = f"{scenario.name[:28]:<28}"
            row += "".join(f"{totals.get(u, 0.0):>12,.2f}" for u in report.user_counts)
            lines.append(row)
        return "\n".join(lines)

    @staticmethod
    def format_scenario_components(report: AwsScenarioPricingBenchmarkReport) -> str:
        lines: list[str] = ["ARCHITECTURE COMPONENTS BY SCENARIO", ""]
        for scenario in report.scenarios:
            lines.append(f"## {scenario.name} ({scenario.scenario_id})")
            lines.append(f"Feature flags: {scenario.feature_flags}")
            for comp in scenario.architecture_components:
                lines.append(
                    f"  - {comp['component_id']}: {comp['name']} "
                    f"({comp['component_type']}) -> AWS {comp['aws_service']}"
                )
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def format_usage_assumptions(
        report: AwsScenarioPricingBenchmarkReport,
        *,
        users: int = 1_000,
    ) -> str:
        lines: list[str] = [
            f"LLM / HEURISTIC USAGE ASSUMPTIONS (users={users:,})",
            "",
        ]
        for scenario in report.scenarios:
            run = next((r for r in scenario.rows if r.users == users), None)
            if run is None:
                continue
            lines.append(f"## {scenario.name} — source: {run.inference_source}")
            for comp in run.components:
                lines.append(f"  [{comp.component_id}] AWS {comp.aws_service} (${comp.subtotal_usd:,.2f})")
                if comp.behavioral_assumptions:
                    lines.append("    Behavioral:")
                    for a in comp.behavioral_assumptions:
                        lines.append(
                            f"      {a.key}={a.value} {a.unit} ({a.confidence}) — {a.reasoning}"
                        )
                if comp.resolved_assumptions:
                    lines.append("    Resolved:")
                    for a in comp.resolved_assumptions:
                        lines.append(
                            f"      {a.key}={a.value} {a.unit} ({a.confidence}) — {a.reasoning}"
                        )
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def format_component_breakdown_table(
        report: AwsScenarioPricingBenchmarkReport,
        *,
        users: int = 1_000,
    ) -> str:
        lines = [
            f"COMPONENT BREAKDOWN AT {users:,} USERS (monthly USD)",
            "",
        ]
        for scenario in report.scenarios:
            run = next((r for r in scenario.rows if r.users == users), None)
            if run is None:
                continue
            lines.append(f"## {scenario.name}")
            for comp in run.components:
                lines.append(f"  {comp.component_id:<16} {comp.aws_service:<16} ${comp.subtotal_usd:>10,.2f}")
            lines.append(f"  {'TOTAL':<16} {'':<16} ${run.total_usd:>10,.2f}")
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def format_full_report(cls, report: AwsScenarioPricingBenchmarkReport) -> str:
        sections = [
            cls.format_summary_table(report),
            "",
            cls.format_scenario_components(report),
            cls.format_component_breakdown_table(report, users=1_000),
            cls.format_usage_assumptions(report, users=1_000),
        ]
        return "\n".join(sections)

    @staticmethod
    def to_serializable(report: AwsScenarioPricingBenchmarkReport) -> dict[str, Any]:
        return report.model_dump()
