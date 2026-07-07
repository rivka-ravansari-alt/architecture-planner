"""Run and report the full GCP pricing pipeline for verification."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.gcp.cost_calculator import GcpCostCalculator
from app.pricing.gcp.coverage import is_gcp_service_fully_supported
from app.pricing.gcp.free_tier import FreeTierPoolState, apply_project_free_tier
from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.gcp.sku_quantities import calculate_gcp_sku_quantities
from app.pricing.gcp.ui_only import is_gcp_ui_only_service
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.pricing.gcp.project_costing import build_ui_only_component_result
from app.pricing.schemas import (
    ComponentCostResult,
    ComponentPricingInput,
    ComponentSkuResult,
    GcpServicePricingModel,
    MissingAssumption,
    MissingCatalogPrice,
    SkuCostLine,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)
from app.schemas.domain import MappedComponent

InferenceMode = Literal["llm", "heuristic"]


class ArchitectureInputSummary(BaseModel):
    component_id: str
    component_name: str
    component_type: str
    optional: bool
    order: int
    gcp_mapping: str


class SkuVerificationLine(BaseModel):
    sku_key: str
    unit: str
    formula: str = ""
    input_values_used: dict[str, int | float | str | bool] = Field(default_factory=dict)
    raw_quantity: float | None = None
    tier_included_quantity: float = 0.0
    free_tier_deducted: float = 0.0
    billable_quantity: float = 0.0
    catalog_role: str | None = None
    unit_price_usd: float | None = None
    catalog_usage_unit: str | None = None
    billable_units: float | None = None
    sku_cost_usd: float | None = None
    warnings: list[str] = Field(default_factory=list)
    missing_price_reason: str | None = None


class ComponentVerificationReport(BaseModel):
    architecture: ArchitectureInputSummary
    gcp_service: str
    catalog_service_name: str
    usage_assumptions: dict[str, int | float | str | bool] = Field(default_factory=dict)
    behavioral_assumptions: list[UsageAssumption] = Field(default_factory=list)
    resolved_assumptions: list[UsageAssumption] = Field(default_factory=list)
    missing_assumptions: list[MissingAssumption] = Field(default_factory=list)
    raw_sku_quantities: list[SkuQuantity] = Field(default_factory=list)
    included_usage: list[dict[str, Any]] = Field(default_factory=list)
    billable_sku_quantities: list[SkuQuantity] = Field(default_factory=list)
    sku_lines: list[SkuVerificationLine] = Field(default_factory=list)
    subtotal_usd: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    ready: bool = True
    pricing_status: str = "supported"
    unsupported_reason: str | None = None


class GcpPricingVerificationReport(BaseModel):
    project_name: str
    expected_users: str
    stage: str
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    inference_source: str = ""
    components: list[ComponentVerificationReport] = Field(default_factory=list)
    pool_summary: dict[str, Any] = Field(default_factory=dict)
    total_usd: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    supported_component_count: int = 0
    unsupported_component_count: int = 0
    ui_only_component_count: int = 0


class GcpPricingVerificationRunner:
    """Execute stages 1–8 and produce a structured verification report."""

    def __init__(
        self,
        cost_calculator: GcpCostCalculator,
        *,
        usage_inference: GcpUsageInferenceEngine | None = None,
        inference_mode: InferenceMode = "heuristic",
    ) -> None:
        self._cost_calculator = cost_calculator
        self._usage_inference = usage_inference or GcpUsageInferenceEngine(
            inference_mode=inference_mode,
        )
        self._default_inference_mode = inference_mode

    def run(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
        inference_mode: InferenceMode | None = None,
        pricing_inputs: list[ComponentPricingInput] | None = None,
        inference_source: str | None = None,
    ) -> GcpPricingVerificationReport:
        flags = feature_flags or {}
        if pricing_inputs is None:
            mode = inference_mode or self._default_inference_mode
            pricing_inputs = self._usage_inference.infer_components(
                project,
                components,
                feature_flags=flags,
                inference_mode=mode,
            )
            inference_source = mode if mode == "heuristic" else "llm"
        inputs_by_id = {item.component_id: item for item in pricing_inputs}
        pool = FreeTierPoolState()

        component_reports: list[ComponentVerificationReport] = []
        all_warnings: list[str] = []
        all_missing: list[MissingCatalogPrice] = []
        total = 0.0
        supported = 0
        unsupported = 0
        ui_only = 0

        for component in sorted(components, key=lambda item: item.order):
            gcp_name = component.cloud.get("gcp")
            if not gcp_name:
                continue
            if is_gcp_ui_only_service(str(gcp_name)):
                side = build_ui_only_component_result(component, str(gcp_name))
                component_reports.append(
                    ComponentVerificationReport(
                        architecture=ArchitectureInputSummary(
                            component_id=component.key,
                            component_name=component.name,
                            component_type=component.component_type,
                            optional=component.optional,
                            order=component.order,
                            gcp_mapping=str(gcp_name),
                        ),
                        gcp_service=side.service,
                        catalog_service_name=side.catalog_service_name,
                        warnings=list(side.warnings),
                        ready=True,
                        pricing_status="ui_only",
                    )
                )
                ui_only += 1
                all_warnings.extend(side.warnings)
                continue
            if not is_gcp_service_fully_supported(str(gcp_name)):
                report = self._unsupported_component_report(component, str(gcp_name))
                component_reports.append(report)
                unsupported += 1
                all_warnings.extend(report.warnings)
                continue

            report = self._verify_component(
                component,
                inputs_by_id.get(component.key),
                pool,
            )
            if report is None:
                continue
            component_reports.append(report)
            if report.pricing_status == "supported":
                supported += 1
                total += report.subtotal_usd
            else:
                unsupported += 1
            all_warnings.extend(report.warnings)
            all_missing.extend(report.missing_prices)

        return GcpPricingVerificationReport(
            project_name=project.name,
            expected_users=project.expected_users or "",
            stage=project.stage or "",
            feature_flags=flags,
            inference_source=inference_source or "",
            components=component_reports,
            pool_summary=pool.summary(),
            total_usd=round(total, 2),
            warnings=all_warnings,
            missing_prices=all_missing,
            supported_component_count=supported,
            unsupported_component_count=unsupported,
            ui_only_component_count=ui_only,
        )

    def _unsupported_component_report(
        self,
        component: MappedComponent,
        gcp_name: str,
    ) -> ComponentVerificationReport:
        from app.pricing.gcp.coverage import unsupported_reason_for_service

        reason, _missing = unsupported_reason_for_service(gcp_name)
        return ComponentVerificationReport(
            architecture=ArchitectureInputSummary(
                component_id=component.key,
                component_name=component.name,
                component_type=component.component_type,
                optional=component.optional,
                order=component.order,
                gcp_mapping=gcp_name,
            ),
            gcp_service=gcp_name,
            catalog_service_name=gcp_name,
            warnings=[reason],
            ready=False,
            pricing_status="unsupported",
            unsupported_reason=reason,
        )

    def _verify_component(
        self,
        component: MappedComponent,
        pricing_input: ComponentPricingInput | None,
        pool: FreeTierPoolState,
    ) -> ComponentVerificationReport | None:
        gcp_name = component.cloud.get("gcp")
        if not gcp_name:
            return None

        model = get_gcp_pricing_model(str(gcp_name))
        if model is None or pricing_input is None:
            return None

        resolution_resolved = pricing_input.resolved
        usage_assumptions = {item.key: item.value for item in resolution_resolved}

        raw = calculate_gcp_sku_quantities(model, resolution_resolved)
        adjusted = apply_project_free_tier(
            model,
            raw,
            pool,
            resolved=resolution_resolved,
        )
        sku_result = ComponentSkuResult(
            component_id=component.key,
            service=adjusted.service,
            quantities=adjusted.quantities,
            included_usage=adjusted.included_usage,
            missing=adjusted.missing,
            ready=adjusted.ready,
            resolved=resolution_resolved,
            behavioral_assumptions=pricing_input.behavioral_assumptions,
            warnings=adjusted.warnings,
        )
        cost = self._cost_calculator.calculate_component(model, sku_result)

        sku_lines = self._merge_sku_lines(raw, adjusted, cost)
        included_usage = [item.model_dump(mode="json") for item in adjusted.included_usage]

        return ComponentVerificationReport(
            architecture=ArchitectureInputSummary(
                component_id=component.key,
                component_name=component.name,
                component_type=component.component_type,
                optional=component.optional,
                order=component.order,
                gcp_mapping=str(gcp_name),
            ),
            gcp_service=model.service,
            catalog_service_name=model.catalog_service_name,
            usage_assumptions=usage_assumptions,
            behavioral_assumptions=list(pricing_input.behavioral_assumptions),
            resolved_assumptions=resolution_resolved,
            missing_assumptions=raw.missing,
            raw_sku_quantities=raw.quantities,
            included_usage=included_usage,
            billable_sku_quantities=adjusted.quantities,
            sku_lines=sku_lines,
            subtotal_usd=cost.subtotal_usd,
            warnings=list(adjusted.warnings) + list(cost.warnings),
            missing_prices=cost.missing_prices,
            ready=adjusted.ready and cost.ready,
            pricing_status=cost.pricing_status,
        )

    @staticmethod
    def _merge_sku_lines(
        raw: SkuQuantityResult,
        adjusted: ComponentSkuResult,
        cost: ComponentCostResult,
    ) -> list[SkuVerificationLine]:
        raw_by_key = {item.sku_key: item for item in raw.quantities}
        billable_by_key = {item.sku_key: item for item in adjusted.quantities}
        cost_by_key = {item.sku_key: item for item in cost.line_items}
        missing_by_key = {item.sku_key: item for item in cost.missing_prices}

        tier_included: dict[str, float] = {}
        for item in raw.included_usage:
            tier_included[item.sku_key] = tier_included.get(item.sku_key, 0.0) + item.quantity
        for item in adjusted.included_usage:
            tier_included[item.sku_key] = tier_included.get(item.sku_key, 0.0) + item.quantity

        sku_keys: list[str] = []
        for key in raw_by_key | billable_by_key | cost_by_key | missing_by_key:
            if key not in sku_keys:
                sku_keys.append(key)

        lines: list[SkuVerificationLine] = []
        for sku_key in sku_keys:
            raw_qty = raw_by_key.get(sku_key)
            billable_qty = billable_by_key.get(sku_key)
            cost_line: SkuCostLine | None = cost_by_key.get(sku_key)
            missing = missing_by_key.get(sku_key)

            warnings: list[str] = []
            if raw_qty and raw_qty.warnings:
                warnings.extend(raw_qty.warnings)
            if billable_qty and billable_qty.warnings:
                for warning in billable_qty.warnings:
                    if warning not in warnings:
                        warnings.append(warning)
            if cost_line and cost_line.warnings:
                for warning in cost_line.warnings:
                    if warning not in warnings:
                        warnings.append(warning)

            lines.append(
                SkuVerificationLine(
                    sku_key=sku_key,
                    unit=(billable_qty or raw_qty).unit if (billable_qty or raw_qty) else "",
                    formula=(raw_qty or billable_qty).formula if (raw_qty or billable_qty) else "",
                    input_values_used=(raw_qty or billable_qty).input_values_used
                    if (raw_qty or billable_qty)
                    else {},
                    raw_quantity=(
                        raw_qty.raw_quantity
                        if raw_qty and raw_qty.raw_quantity is not None
                        else raw_qty.quantity
                    )
                    if raw_qty
                    else None,
                    tier_included_quantity=tier_included.get(sku_key, 0.0),
                    free_tier_deducted=(billable_qty or raw_qty).free_tier_deducted
                    if (billable_qty or raw_qty)
                    else 0.0,
                    billable_quantity=billable_qty.quantity if billable_qty else 0.0,
                    catalog_role=cost_line.catalog_role
                    if cost_line
                    else missing.catalog_role
                    if missing
                    else None,
                    unit_price_usd=cost_line.unit_price_usd if cost_line else None,
                    catalog_usage_unit=cost_line.usage_unit if cost_line else None,
                    billable_units=cost_line.billable_units if cost_line else None,
                    sku_cost_usd=cost_line.monthly_cost_usd if cost_line else None,
                    warnings=warnings,
                    missing_price_reason=missing.reason if missing else None,
                )
            )
        return lines


def pricing_completeness(report: GcpPricingVerificationReport) -> str:
    if report.unsupported_component_count:
        return "partial"
    if report.missing_prices:
        return "partial"
    unpriced = [
        component
        for component in report.components
        if component.pricing_status == "supported"
        and any(
            line.billable_quantity > 0 and line.sku_cost_usd is None
            for line in component.sku_lines
        )
    ]
    if unpriced:
        return "partial"
    return "complete"


def build_validation_checks(report: GcpPricingVerificationReport) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    component_sum = round(sum(item.subtotal_usd for item in report.components), 2)
    if abs(component_sum - report.total_usd) < 0.02:
        checks.append(
            {
                "rule_id": "total_equals_components",
                "status": "pass",
                "message": f"Total ${report.total_usd:,.2f} equals component sum ${component_sum:,.2f}.",
            }
        )
    else:
        checks.append(
            {
                "rule_id": "total_equals_components",
                "status": "fail",
                "message": f"Total ${report.total_usd:,.2f} != component sum ${component_sum:,.2f}.",
            }
        )

    negative = [
        line.sku_key
        for component in report.components
        for line in component.sku_lines
        if line.billable_quantity < 0 or (line.raw_quantity or 0) < 0
    ]
    checks.append(
        {
            "rule_id": "no_negative_quantities",
            "status": "pass" if not negative else "fail",
            "message": "All SKU quantities are non-negative."
            if not negative
            else f"Negative quantities: {', '.join(negative)}",
        }
    )

    silent_zero = [
        f"{component.architecture.component_id}/{line.sku_key}"
        for component in report.components
        for line in component.sku_lines
        if line.billable_quantity > 0 and line.sku_cost_usd is None and not line.missing_price_reason
    ]
    checks.append(
        {
            "rule_id": "no_silent_zero",
            "status": "pass" if not silent_zero else "fail",
            "message": "No billable SKU silently priced at $0."
            if not silent_zero
            else f"Silent $0 SKUs: {', '.join(silent_zero)}",
        }
    )

    if report.missing_prices:
        checks.append(
            {
                "rule_id": "missing_catalog_prices",
                "status": "warn",
                "message": f"{len(report.missing_prices)} missing catalog price(s) reported.",
            }
        )
    else:
        checks.append(
            {
                "rule_id": "missing_catalog_prices",
                "status": "pass",
                "message": "No missing catalog prices.",
            }
        )

    free_tier_lines = [
        f"{component.architecture.component_id}/{line.sku_key}"
        for component in report.components
        for line in component.sku_lines
        if line.free_tier_deducted > 0
    ]
    checks.append(
        {
            "rule_id": "free_tier_applied",
            "status": "pass" if free_tier_lines or report.total_usd == 0 else "warn",
            "message": f"Free tier applied to {len(free_tier_lines)} SKU line(s)."
            if free_tier_lines
            else "No free tier deductions recorded.",
        }
    )

    completeness = pricing_completeness(report)
    checks.append(
        {
            "rule_id": "pricing_completeness",
            "status": "pass" if completeness == "complete" else "warn",
            "message": f"Pricing completeness: {completeness}.",
        }
    )

    if report.warnings:
        checks.append(
            {
                "rule_id": "warnings",
                "status": "warn",
                "message": f"{len(report.warnings)} warning(s): {' | '.join(report.warnings[:3])}",
            }
        )

    return checks
