"""GCP catalog pricing benchmark across benchmark scenarios and user counts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.clients.ai_client import BaseAIClient
from app.models import Project
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS, USER_COUNT_TO_PROJECT_LABEL
from app.pricing.azure.scenarios import (
    AI_CHAT,
    AI_DOCUMENT_OCR,
    ECOMMERCE,
    SELF_ESTEEM_HABIT,
    SIMPLE_CRUD_SAAS,
    BenchmarkScenario,
)
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.gcp.scenarios import gcp_scenario_components, normalize_gcp_service_aliases
from app.pricing.usage.service import UsageAssumptionsService
from app.schemas.domain import MappedComponent

InferenceMode = Literal["llm", "heuristic"]

GCP_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    SIMPLE_CRUD_SAAS,
    SELF_ESTEEM_HABIT,
    ECOMMERCE,
    AI_CHAT,
    AI_DOCUMENT_OCR,
)

_GCP_SERVICE_ALIASES = {
    "pub/sub": "Cloud Pub/Sub",
    "cloud pubsub": "Cloud Pub/Sub",
}


def normalize_gcp_components(components: list[MappedComponent]) -> list[MappedComponent]:
    """Map catalog display names to GcpPricingModelRegistry keys."""
    normalized: list[MappedComponent] = []
    for component in components:
        item = deepcopy(component)
        gcp_name = str(item.cloud.get("gcp", ""))
        alias = _GCP_SERVICE_ALIASES.get(gcp_name.strip().casefold())
        if alias:
            item.cloud = dict(item.cloud)
            item.cloud["gcp"] = alias
        else:
            resolved = normalize_gcp_service_aliases(gcp_name)
            if resolved != gcp_name:
                item.cloud = dict(item.cloud)
                item.cloud["gcp"] = resolved
        normalized.append(item)
    return normalized


def scenario_component_summary(scenario: BenchmarkScenario) -> list[dict[str, str]]:
    return [
        {
            "component_id": spec.key,
            "name": spec.name,
            "component_type": spec.component_type,
            "gcp_service": spec.gcp_service,
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
    gcp_service: str
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


class GcpScenarioPricingBenchmarkReport(BaseModel):
    provider: str = "gcp"
    inference_mode: InferenceMode
    user_counts: list[int] = Field(default_factory=lambda: list(BENCHMARK_USER_COUNTS))
    scenarios: list[ScenarioBenchmarkReport] = Field(default_factory=list)


@dataclass
class GcpScenarioPricingBenchmark:
    """Run GCP catalog pricing for benchmark scenarios with usage inference."""

    pipeline: GcpProjectCostingPipeline
    usage_service: UsageAssumptionsService
    inference_mode: InferenceMode = "llm"
    scenarios: tuple[BenchmarkScenario, ...] = GCP_BENCHMARK_SCENARIOS
    user_counts: tuple[int, ...] = BENCHMARK_USER_COUNTS

    def run(self) -> GcpScenarioPricingBenchmarkReport:
        scenario_reports: list[ScenarioBenchmarkReport] = []
        for scenario in self.scenarios:
            components = normalize_gcp_components(gcp_scenario_components(scenario))
            rows: list[UserCountRunRow] = []
            for users in self.user_counts:
                rows.append(self._run_user_count(scenario, components, users))
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
        return GcpScenarioPricingBenchmarkReport(
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
            provider="gcp",
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
                    gcp_service=component_input.cloud_service,
                    subtotal_usd=round(cost_component.subtotal_usd, 2) if cost_component else 0.0,
                    behavioral_assumptions=_serialize(component_input.behavioral_assumptions),
                    resolved_assumptions=_serialize(component_input.resolved),
                )
            )
        return details


def build_usage_service(
    *,
    ai_client: BaseAIClient | None = None,
    inference_mode: InferenceMode = "heuristic",
) -> UsageAssumptionsService:
    if inference_mode == "heuristic":
        return UsageAssumptionsService(inference_mode="heuristic")
    return UsageAssumptionsService(ai_client=ai_client, inference_mode="llm")


class GcpScenarioPricingBenchmarkFormatter:
    """Text formatter for GCP scenario benchmark reports."""

    @staticmethod
    def format_summary_table(report: GcpScenarioPricingBenchmarkReport) -> str:
        lines = [
            "GCP SCENARIO PRICING BENCHMARK (monthly USD)",
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
    def format_scenario_components(report: GcpScenarioPricingBenchmarkReport) -> str:
        lines: list[str] = ["ARCHITECTURE COMPONENTS BY SCENARIO", ""]
        for scenario in report.scenarios:
            lines.append(f"## {scenario.name} ({scenario.scenario_id})")
            lines.append(f"Feature flags: {scenario.feature_flags}")
            for comp in scenario.architecture_components:
                lines.append(
                    f"  - {comp['component_id']}: {comp['name']} "
                    f"({comp['component_type']}) -> GCP {comp['gcp_service']}"
                )
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def format_full_report(cls, report: GcpScenarioPricingBenchmarkReport) -> str:
        return "\n\n".join(
            [
                cls.format_summary_table(report),
                cls.format_scenario_components(report),
            ]
        )

    @staticmethod
    def to_serializable(report: GcpScenarioPricingBenchmarkReport) -> dict[str, Any]:
        return report.model_dump()
