"""SKU-level pricing coverage audit for AWS catalog pricing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.models import Project
from app.pricing.aws.benchmark import build_usage_service, normalize_aws_components
from app.pricing.aws.cost_calculator import AwsCostCalculator
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.project_pricing import calculate_project_aws_sku_quantities
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.aws.scenarios import AWS_TWENTY_SCENARIOS, twenty_scenario_components
from app.pricing.aws.sku_roles import AwsSkuRoleResolver
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.pricing.azure.benchmark import USER_COUNT_TO_PROJECT_LABEL
from app.pricing.azure.scenarios import BenchmarkScenario
from app.pricing.schemas import (
    ComponentCostResult,
    ComponentPricingInput,
    ComponentSkuResult,
    MissingCatalogPrice,
    SkuCostLine,
    SkuQuantity,
)
from app.pricing.usage.service import UsageAssumptionsService

SkuAuditStatus = Literal[
    "priced",
    "free_tier_zero",
    "no_usage",
    "missing_role",
    "missing_catalog_price",
    "scaling_failed",
    "not_calculated",
]

PRIORITY_SERVICES: tuple[str, ...] = (
    "Lambda",
    "API Gateway",
    "S3",
    "RDS",
    "DynamoDB",
    "CloudFront",
    "Application Load Balancer",
    "ECS Fargate",
    "Bedrock",
    "CloudWatch",
    "Secrets Manager",
    "SNS",
    "SQS",
)


@dataclass
class SkuAuditLine:
    service: str
    component_id: str
    component_name: str
    scenario_name: str
    sku_key: str
    status: SkuAuditStatus
    raw_quantity: float
    billable_quantity: float
    unit: str
    catalog_roles: list[str]
    catalog_role_used: str | None
    unit_price_usd: float | None
    usage_unit: str | None
    final_cost_usd: float
    formula: str
    reason: str = ""


@dataclass
class ServiceSkuSummary:
    service: str
    total_lines: int = 0
    priced: int = 0
    free_tier_zero: int = 0
    scaling_failed: int = 0
    missing_catalog: int = 0
    missing_role: int = 0
    not_calculated: int = 0
    missing_cost_usd_estimate: float = 0.0


@dataclass
class AwsSkuPricingAuditReport:
    users: int
    inference_mode: str
    scenario_count: int
    lines: list[SkuAuditLine] = field(default_factory=list)
    by_service: dict[str, ServiceSkuSummary] = field(default_factory=dict)
    partial_components: list[str] = field(default_factory=list)
    underpriced_scenarios: list[str] = field(default_factory=list)


class AwsSkuPricingAuditor:
    """Audit calculated vs priced SKUs for benchmark scenarios."""

    def __init__(
        self,
        pipeline: AwsProjectCostingPipeline,
        usage_service: UsageAssumptionsService,
        calculator: AwsCostCalculator,
        *,
        inference_mode: str = "heuristic",
        users: int = 1_000,
        scenarios: tuple[BenchmarkScenario, ...] = AWS_TWENTY_SCENARIOS,
    ) -> None:
        self._pipeline = pipeline
        self._usage_service = usage_service
        self._calculator = calculator
        self._inference_mode = inference_mode
        self._users = users
        self._scenarios = scenarios
        self._role_resolver = AwsSkuRoleResolver()

    def run(self) -> AwsSkuPricingAuditReport:
        report = AwsSkuPricingAuditReport(
            users=self._users,
            inference_mode=self._inference_mode,
            scenario_count=len(self._scenarios),
        )
        for scenario in self._scenarios:
            report.lines.extend(self._audit_scenario(scenario))
        report.by_service = _summarize_by_service(report.lines)
        report.partial_components = _partial_component_labels(report.lines)
        report.underpriced_scenarios = _underpriced_scenarios(report.lines)
        return report

    def _audit_scenario(self, scenario: BenchmarkScenario) -> list[SkuAuditLine]:
        components = normalize_aws_components(twenty_scenario_components(scenario))
        component_names = {spec.key: spec.name for spec in scenario.components}
        project = Project(
            name=scenario.name,
            description=scenario.product_description,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[self._users],
            stage=scenario.stage,
        )
        inference = self._usage_service.infer(
            project,
            components,
            provider="aws",
            feature_flags=scenario.feature_flags,
            inference_mode=self._inference_mode,  # type: ignore[arg-type]
        )
        pricing_inputs = list(inference.components)
        quantity_result = calculate_project_aws_sku_quantities(pricing_inputs)
        cost_result = self._pipeline.calculate(
            project,
            components,
            pricing_inputs=pricing_inputs,
            feature_flags=scenario.feature_flags,
        )

        sku_by_id = {item.component_id: item for item in quantity_result.components}
        cost_by_id = {item.component_id: item for item in cost_result.components}
        lines: list[SkuAuditLine] = []

        for component in components:
            aws_service = str(component.cloud.get("aws", ""))
            if aws_service not in {s for s in PRIORITY_SERVICES} and aws_service not in {
                line.service for line in lines
            }:
                pass
            model = get_aws_pricing_model(aws_service)
            if model is None:
                continue

            sku_component = sku_by_id.get(component.key)
            cost_component = cost_by_id.get(component.key)
            lines.extend(
                self._audit_component(
                    scenario=scenario,
                    component_id=component.key,
                    component_name=component_names.get(component.key, component.name),
                    model_service=model.service,
                    catalog_service=model.catalog_service_name,
                    sku_component=sku_component,
                    cost_component=cost_component,
                )
            )
        return lines

    def _audit_component(
        self,
        *,
        scenario: BenchmarkScenario,
        component_id: str,
        component_name: str,
        model_service: str,
        catalog_service: str,
        sku_component: ComponentSkuResult | None,
        cost_component: ComponentCostResult | None,
    ) -> list[SkuAuditLine]:
        model = get_aws_pricing_model(model_service)
        if model is None:
            return []

        quantities_by_key: dict[str, SkuQuantity] = {}
        if sku_component is not None:
            quantities_by_key = {q.sku_key: q for q in sku_component.quantities}

        cost_by_key: dict[str, SkuCostLine] = {}
        missing_by_key: dict[str, list[MissingCatalogPrice]] = {}
        if cost_component is not None:
            cost_by_key = {line.sku_key: line for line in cost_component.line_items}
            for missing in cost_component.missing_prices:
                missing_by_key.setdefault(missing.sku_key, []).append(missing)

        lines: list[SkuAuditLine] = []
        for sku_def in model.pricing_model.calculated_skus:
            sku_key = sku_def.key
            quantity = quantities_by_key.get(sku_key)
            cost_line = cost_by_key.get(sku_key)
            roles = self._role_resolver.resolve(model, sku_key)

            if quantity is None:
                lines.append(
                    SkuAuditLine(
                        service=model_service,
                        component_id=component_id,
                        component_name=component_name,
                        scenario_name=scenario.name,
                        sku_key=sku_key,
                        status="not_calculated",
                        raw_quantity=0.0,
                        billable_quantity=0.0,
                        unit=sku_def.unit,
                        catalog_roles=list(roles),
                        catalog_role_used=None,
                        unit_price_usd=None,
                        usage_unit=None,
                        final_cost_usd=0.0,
                        formula=sku_def.derivation,
                        reason="SKU not produced by quantity calculator.",
                    )
                )
                continue

            raw_qty = quantity.raw_quantity if quantity.raw_quantity is not None else quantity.quantity
            billable = quantity.quantity

            if raw_qty <= 0:
                status: SkuAuditStatus = "no_usage"
                reason = "Zero calculated usage."
            elif billable <= 0:
                status = "free_tier_zero"
                reason = (
                    f"{raw_qty:,.0f} {quantity.unit} calculated; "
                    f"${quantity.free_tier_deducted:,.0f} deducted by free tier."
                )
            elif cost_line is not None:
                status = "priced"
                reason = cost_line.formula_note
            elif missing_by_key.get(sku_key):
                first = missing_by_key[sku_key][0]
                if first.catalog_role is None:
                    status = "missing_role"
                elif "scale" in first.reason.casefold():
                    status = "scaling_failed"
                else:
                    status = "missing_catalog_price"
                reason = first.reason
            elif not roles:
                status = "missing_role"
                reason = "No catalog role mapping for sku_key."
            else:
                status = "scaling_failed"
                reason = "Billable quantity present but no cost line produced."

            unit_price = cost_line.unit_price_usd if cost_line else None
            usage_unit = cost_line.usage_unit if cost_line else None
            role_used = cost_line.catalog_role if cost_line else None

            lines.append(
                SkuAuditLine(
                    service=model_service,
                    component_id=component_id,
                    component_name=component_name,
                    scenario_name=scenario.name,
                    sku_key=sku_key,
                    status=status,
                    raw_quantity=raw_qty,
                    billable_quantity=billable,
                    unit=quantity.unit,
                    catalog_roles=list(roles),
                    catalog_role_used=role_used,
                    unit_price_usd=unit_price,
                    usage_unit=usage_unit,
                    final_cost_usd=cost_line.monthly_cost_usd if cost_line else 0.0,
                    formula=quantity.formula or sku_def.derivation,
                    reason=reason,
                )
            )
        return lines


def _summarize_by_service(lines: list[SkuAuditLine]) -> dict[str, ServiceSkuSummary]:
    summaries: dict[str, ServiceSkuSummary] = {}
    for line in lines:
        summary = summaries.setdefault(line.service, ServiceSkuSummary(service=line.service))
        summary.total_lines += 1
        if line.status == "priced":
            summary.priced += 1
        elif line.status == "free_tier_zero":
            summary.free_tier_zero += 1
        elif line.status == "scaling_failed":
            summary.scaling_failed += 1
        elif line.status == "missing_catalog_price":
            summary.missing_catalog += 1
        elif line.status == "missing_role":
            summary.missing_role += 1
        elif line.status == "not_calculated":
            summary.not_calculated += 1
    return summaries


def _partial_component_labels(lines: list[SkuAuditLine]) -> list[str]:
    partial: list[str] = []
    grouped: dict[tuple[str, str, str], list[SkuAuditLine]] = {}
    for line in lines:
        key = (line.scenario_name, line.component_id, line.service)
        grouped.setdefault(key, []).append(line)

    for (scenario, component_id, service), sku_lines in grouped.items():
        problems = [
            item
            for item in sku_lines
            if item.status
            in {"scaling_failed", "missing_catalog_price", "missing_role", "not_calculated"}
            or (item.billable_quantity > 0 and item.status != "priced")
        ]
        if problems:
            partial.append(f"{scenario} / {component_id} ({service}): {len(problems)} SKU gap(s)")
    return sorted(partial)


def _underpriced_scenarios(lines: list[SkuAuditLine]) -> list[str]:
    """Scenarios where priority services have billable SKUs that failed to price."""
    scenarios: set[str] = set()
    for line in lines:
        if line.service not in PRIORITY_SERVICES:
            continue
        if line.billable_quantity > 0 and line.status != "priced":
            scenarios.add(
                f"{line.scenario_name}: {line.service}.{line.sku_key} "
                f"({line.billable_quantity:,.0f} {line.unit}) — {line.status}"
            )
    return sorted(scenarios)


def format_audit_report(report: AwsSkuPricingAuditReport) -> str:
    lines_out: list[str] = [
        "AWS SKU PRICING COVERAGE AUDIT",
        f"Scenarios: {report.scenario_count} | Users: {report.users:,} | Mode: {report.inference_mode}",
        "",
        "SERVICE SUMMARY",
        f"{'Service':<28} {'Priced':>7} {'Free$0':>7} {'ScaleFail':>10} {'MissCat':>8} {'MissRole':>9} {'NotCalc':>8}",
        "-" * 85,
    ]
    for service in PRIORITY_SERVICES:
        summary = report.by_service.get(service)
        if summary is None:
            continue
        lines_out.append(
            f"{service:<28} {summary.priced:>7} {summary.free_tier_zero:>7} "
            f"{summary.scaling_failed:>10} {summary.missing_catalog:>8} "
            f"{summary.missing_role:>9} {summary.not_calculated:>8}"
        )

    lines_out.extend(["", "UNDERPRICED / INCOMPLETE SKU LINES (billable qty not priced)", ""])
    if report.underpriced_scenarios:
        lines_out.extend(f"  - {item}" for item in report.underpriced_scenarios)
    else:
        lines_out.append("  None — all billable SKU quantities produced cost lines.")

    lines_out.extend(["", "PARTIAL COMPONENTS", ""])
    if report.partial_components:
        lines_out.extend(f"  - {item}" for item in report.partial_components[:40])
        if len(report.partial_components) > 40:
            lines_out.append(f"  ... and {len(report.partial_components) - 40} more")
    else:
        lines_out.append("  None")

    lines_out.extend(["", "DETAIL — priority services with gaps only", ""])
    gap_lines = [
        line
        for line in report.lines
        if line.service in PRIORITY_SERVICES
        and line.status
        in {"scaling_failed", "missing_catalog_price", "missing_role", "not_calculated", "free_tier_zero"}
        and (line.raw_quantity > 0 or line.status != "no_usage")
    ]
    for line in gap_lines[:60]:
        lines_out.append(
            f"  [{line.status}] {line.scenario_name} / {line.component_name} ({line.service}) "
            f"sku={line.sku_key} raw={line.raw_quantity:,.0f} billable={line.billable_quantity:,.0f} "
            f"roles={line.catalog_roles} cost=${line.final_cost_usd:,.2f}"
        )
        if line.reason:
            lines_out.append(f"      -> {line.reason}")
    if len(gap_lines) > 60:
        lines_out.append(f"  ... and {len(gap_lines) - 60} more gap lines")

    return "\n".join(lines_out)


def build_auditor(
    *,
    inference_mode: str = "heuristic",
    users: int = 1_000,
    catalog: str = "firestore",
) -> AwsSkuPricingAuditor:
    from app.pricing.aws.scenario_excel_export import build_aws_cost_calculator

    calculator = build_aws_cost_calculator(catalog=catalog)  # type: ignore[arg-type]
    pipeline = AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)
    usage_service = build_usage_service(inference_mode=inference_mode)  # type: ignore[arg-type]
    return AwsSkuPricingAuditor(
        pipeline,
        usage_service,
        calculator,
        inference_mode=inference_mode,
        users=users,
    )
