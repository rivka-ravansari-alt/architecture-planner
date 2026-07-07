"""Run and report the full Azure pricing pipeline for verification."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.models import Project
from app.pricing.azure.cost_calculator import AzureCostCalculator
from app.pricing.azure.free_tier import FreeTierPoolState, apply_project_free_tier
from app.pricing.azure.registry import get_azure_pricing_model
from app.pricing.azure.sku_quantities import calculate_azure_sku_quantities
from app.pricing.azure.usage_inference import AzureUsageInferenceEngine, InferenceMode
from app.pricing.schemas import (
    AzureServicePricingModel,
    ComponentCostResult,
    ComponentPricingInput,
    ComponentSkuResult,
    MissingAssumption,
    MissingCatalogPrice,
    SkuCostLine,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)
from app.schemas.domain import MappedComponent


class ArchitectureInputSummary(BaseModel):
    """Stage 1 — component as mapped for Azure pricing."""

    component_id: str
    component_name: str
    component_type: str
    optional: bool
    order: int
    azure_mapping: str


class SkuVerificationLine(BaseModel):
    """Merged view of stages 4–8 for one SKU."""

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
    """Full pipeline trace for one Azure-mapped component."""

    architecture: ArchitectureInputSummary
    azure_service: str
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


class AzurePricingVerificationReport(BaseModel):
    """Project-level Azure pricing verification output."""

    project_name: str
    expected_users: str
    stage: str
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    components: list[ComponentVerificationReport] = Field(default_factory=list)
    pool_summary: dict[str, Any] = Field(default_factory=dict)
    total_usd: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)


class AzurePricingVerificationRunner:
    """Execute stages 1–8 and produce a structured verification report."""

    def __init__(
        self,
        cost_calculator: AzureCostCalculator,
        *,
        usage_inference: AzureUsageInferenceEngine | None = None,
        inference_mode: InferenceMode = "heuristic",
    ) -> None:
        self._cost_calculator = cost_calculator
        self._usage_inference = usage_inference or AzureUsageInferenceEngine(
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
    ) -> AzurePricingVerificationReport:
        flags = feature_flags or {}
        mode = inference_mode or self._default_inference_mode
        pricing_inputs = self._usage_inference.infer_components(
            project,
            components,
            feature_flags=flags,
            inference_mode=mode,
        )
        inputs_by_id = {item.component_id: item for item in pricing_inputs}
        pool = FreeTierPoolState()

        component_reports: list[ComponentVerificationReport] = []
        all_warnings: list[str] = []
        all_missing: list[MissingCatalogPrice] = []
        total = 0.0

        for component in sorted(components, key=lambda item: item.order):
            report = self._verify_component(
                component,
                inputs_by_id.get(component.key),
                pool,
            )
            if report is None:
                continue
            component_reports.append(report)
            total += report.subtotal_usd
            all_warnings.extend(report.warnings)
            all_missing.extend(report.missing_prices)

        return AzurePricingVerificationReport(
            project_name=project.name,
            expected_users=project.expected_users or "",
            stage=project.stage or "",
            feature_flags=flags,
            components=component_reports,
            pool_summary=pool.summary(),
            total_usd=total,
            warnings=all_warnings,
            missing_prices=all_missing,
        )

    def _verify_component(
        self,
        component: MappedComponent,
        pricing_input: ComponentPricingInput | None,
        pool: FreeTierPoolState,
    ) -> ComponentVerificationReport | None:
        azure_name = component.cloud.get("azure")
        if not azure_name:
            return None

        model = get_azure_pricing_model(str(azure_name))
        if model is None:
            return None

        if pricing_input is None:
            return None

        resolution_resolved = pricing_input.resolved
        usage_assumptions = {
            item.key: item.value for item in resolution_resolved
        }

        raw = calculate_azure_sku_quantities(model, resolution_resolved)
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
            warnings=adjusted.warnings,
        )
        cost = self._cost_calculator.calculate_component(model, sku_result)

        sku_lines = self._merge_sku_lines(raw, adjusted, cost)
        included_usage = [
            item.model_dump(mode="json") for item in adjusted.included_usage
        ]

        return ComponentVerificationReport(
            architecture=ArchitectureInputSummary(
                component_id=component.key,
                component_name=component.name,
                component_type=component.component_type,
                optional=component.optional,
                order=component.order,
                azure_mapping=str(azure_name),
            ),
            azure_service=model.service,
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
                        if raw_qty.raw_quantity is not None
                        else raw_qty.quantity
                    )
                    if raw_qty
                    else None,
                    tier_included_quantity=tier_included.get(sku_key, 0.0),
                    free_tier_deducted=(billable_qty or raw_qty).free_tier_deducted
                    if (billable_qty or raw_qty)
                    else 0.0,
                    billable_quantity=billable_qty.quantity if billable_qty else 0.0,
                    catalog_role=cost_line.catalog_role if cost_line else missing.catalog_role if missing else None,
                    unit_price_usd=cost_line.unit_price_usd if cost_line else None,
                    catalog_usage_unit=cost_line.usage_unit if cost_line else None,
                    billable_units=cost_line.billable_units if cost_line else None,
                    sku_cost_usd=cost_line.monthly_cost_usd if cost_line else None,
                    warnings=warnings,
                    missing_price_reason=missing.reason if missing else None,
                )
            )
        return lines


class AzurePricingReportFormatter:
    """Render a verification report as human-readable text."""

    def format(self, report: AzurePricingVerificationReport) -> str:
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("AZURE PRICING VERIFICATION REPORT")
        lines.append("=" * 80)
        lines.append(
            f"Project: {report.project_name} | Users: {report.expected_users} | Stage: {report.stage}"
        )
        lines.append(f"Feature flags: {json.dumps(report.feature_flags, sort_keys=True)}")
        lines.append("")

        for index, component in enumerate(report.components, start=1):
            lines.extend(self._format_component(component, index))

        lines.append("=" * 80)
        lines.append("PROJECT SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Free-tier pool summary: {json.dumps(report.pool_summary, indent=2)}")
        lines.append(f"Total monthly cost (USD): ${report.total_usd:,.4f}")
        if report.warnings:
            lines.append("\nProject warnings:")
            for warning in report.warnings:
                lines.append(f"  - {warning}")
        if report.missing_prices:
            lines.append("\nProject missing catalog prices:")
            for item in report.missing_prices:
                lines.append(
                    f"  - {item.catalog_service_name}/{item.sku_key}"
                    f" (role={item.catalog_role}): {item.reason}"
                )
        lines.append("")
        return "\n".join(lines)

    def _format_component(self, component: ComponentVerificationReport, index: int) -> list[str]:
        lines: list[str] = []
        arch = component.architecture
        lines.append("-" * 80)
        lines.append(f"COMPONENT {index}: {arch.component_name} ({arch.component_id})")
        lines.append("-" * 80)

        lines.append("\n[1] Architecture / component input")
        lines.append(f"  type: {arch.component_type}")
        lines.append(f"  optional: {arch.optional}")
        lines.append(f"  order: {arch.order}")
        lines.append(f"  azure mapping: {arch.azure_mapping}")
        lines.append(f"  azure service: {component.azure_service}")
        lines.append(f"  catalog service name: {component.catalog_service_name}")

        lines.append("\n[2] Usage assumptions (inferred from project context)")
        if component.usage_assumptions:
            for key, value in sorted(component.usage_assumptions.items()):
                lines.append(f"  {key}: {_fmt_value(value)}")
        else:
            lines.append("  (none — component skipped or zero usage)")

        lines.append("\n[3] Resolved assumptions")
        for assumption in component.resolved_assumptions:
            lines.append(
                f"  {assumption.key}: {_fmt_value(assumption.value)} "
                f"({assumption.source.value}, {assumption.confidence.value})"
            )
        if component.missing_assumptions:
            lines.append("  missing:")
            for missing in component.missing_assumptions:
                lines.append(f"    - {missing.key}: {missing.reason}")

        lines.append("\n[4] Raw SKU quantities")
        for sku in component.raw_sku_quantities:
            lines.append(f"  {sku.sku_key}: {_fmt_qty(sku.raw_quantity or sku.quantity)} {sku.unit}")
            lines.append(f"    formula: {sku.formula}")

        lines.append("\n[5] Free tier / included usage deducted")
        if component.included_usage:
            for item in component.included_usage:
                lines.append(
                    f"  tier/plan inclusion - {item['sku_key']}: "
                    f"{_fmt_qty(item['quantity'])} {item['unit']} ({item['source']})"
                )
        for line in component.sku_lines:
            if line.free_tier_deducted > 0 or line.tier_included_quantity > 0:
                parts = []
                if line.tier_included_quantity > 0:
                    parts.append(f"tier_included={_fmt_qty(line.tier_included_quantity)}")
                if line.free_tier_deducted > 0:
                    parts.append(f"free_tier_deducted={_fmt_qty(line.free_tier_deducted)}")
                lines.append(f"  {line.sku_key}: {', '.join(parts)}")
        if not component.included_usage and not any(
            line.free_tier_deducted or line.tier_included_quantity for line in component.sku_lines
        ):
            lines.append("  (none)")

        lines.append("\n[6] Billable SKU quantities")
        for line in component.sku_lines:
            lines.append(f"  {line.sku_key}: {_fmt_qty(line.billable_quantity)} {line.unit}")

        lines.append("\n[7] Catalog price lookup")
        for line in component.sku_lines:
            if line.unit_price_usd is not None:
                lines.append(
                    f"  {line.sku_key} -> role {line.catalog_role!r}: "
                    f"${line.unit_price_usd} per {line.catalog_usage_unit}"
                )
            elif line.missing_price_reason:
                lines.append(
                    f"  {line.sku_key} -> MISSING: {line.missing_price_reason}"
                )
            elif line.billable_quantity <= 0:
                lines.append(f"  {line.sku_key}: skipped (zero billable quantity)")

        lines.append("\n[8] Final SKU cost")
        for line in component.sku_lines:
            if line.sku_cost_usd is not None:
                lines.append(
                    f"  {line.sku_key}: {_fmt_qty(line.billable_units)} catalog units x "
                    f"${line.unit_price_usd} = ${line.sku_cost_usd:,.4f}"
                )
            elif line.missing_price_reason and line.billable_quantity > 0:
                lines.append(f"  {line.sku_key}: UNPRICED - {line.missing_price_reason}")

        if component.warnings:
            lines.append("\n  warnings:")
            for warning in component.warnings:
                lines.append(f"    - {warning}")
        if component.missing_prices:
            lines.append("\n  missing prices:")
            for item in component.missing_prices:
                lines.append(
                    f"    - {item.sku_key} (role={item.catalog_role}): {item.reason}"
                )

        lines.append(f"\n  component subtotal (USD): ${component.subtotal_usd:,.4f}")
        lines.append(f"  ready: {component.ready}")
        lines.append("")
        return lines


def _fmt_value(value: int | float | str | bool) -> str:
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int) and abs(value) >= 1000:
        return f"{value:,}"
    return str(value)


def _fmt_qty(value: float | None) -> str:
    if value is None:
        return "0"
    return f"{value:,.4f}".rstrip("0").rstrip(".")
