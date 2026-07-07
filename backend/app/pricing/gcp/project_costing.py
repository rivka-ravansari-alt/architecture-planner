"""End-to-end GCP catalog pricing for a project."""

from __future__ import annotations

from app.models import Project
from app.pricing.gcp.cost_calculator import GcpCostCalculator
from app.pricing.gcp.coverage import is_gcp_service_fully_supported, unsupported_reason_for_service
from app.pricing.gcp.ui_only import is_gcp_ui_only_service, ui_only_note_for_service
from app.pricing.gcp.project_pricing import calculate_project_gcp_sku_quantities
from app.pricing.gcp.registry import get_gcp_pricing_model, normalize_gcp_service_name
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.pricing.schemas import (
    ComponentCostResult,
    ComponentPricingInput,
    GcpServicePricingModel,
    ProjectGcpCostResult,
)
from app.schemas.domain import MappedComponent


def _gcp_mapped_components(components: list[MappedComponent]) -> list[MappedComponent]:
    return [
        component
        for component in sorted(components, key=lambda item: item.order)
        if component.cloud.get("gcp")
    ]


def build_ui_only_component_result(
    component: MappedComponent,
    mapped_service: str,
) -> ComponentCostResult:
    """Build a $0 UI-only result — costs accrue via backing services, not this selection."""
    note = ui_only_note_for_service(mapped_service)
    canonical = normalize_gcp_service_name(mapped_service)
    return ComponentCostResult(
        component_id=component.key,
        service=canonical,
        catalog_service_name=mapped_service,
        subtotal_usd=0.0,
        line_items=[],
        missing_prices=[],
        warnings=[note],
        ready=True,
        pricing_status="ui_only",
        pricing_note=note,
        optional=component.optional,
    )


def build_unsupported_component_result(
    component: MappedComponent,
    mapped_service: str,
) -> ComponentCostResult:
    """Build an explicit unsupported pricing result — never silent $0."""
    reason, missing = unsupported_reason_for_service(mapped_service)
    canonical = normalize_gcp_service_name(mapped_service)
    return ComponentCostResult(
        component_id=component.key,
        service=canonical,
        catalog_service_name=mapped_service,
        subtotal_usd=0.0,
        line_items=[],
        missing_prices=[],
        warnings=[reason],
        ready=False,
        pricing_status="unsupported",
        unsupported_reason=reason,
        missing_implementation=missing,
        optional=component.optional,
    )


class GcpProjectCostingPipeline:
    """End-to-end GCP catalog pricing for a project."""

    def __init__(
        self,
        usage_inference: GcpUsageInferenceEngine,
        cost_calculator: GcpCostCalculator,
    ) -> None:
        self._usage_inference = usage_inference
        self._cost_calculator = cost_calculator

    def calculate(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        pricing_inputs: list[ComponentPricingInput] | None = None,
        feature_flags: dict[str, bool] | None = None,
    ) -> ProjectGcpCostResult:
        gcp_components = _gcp_mapped_components(components)
        if not gcp_components:
            return ProjectGcpCostResult(
                total_usd=0.0,
                warnings=["No GCP-mapped components found for catalog pricing."],
            )

        supported_components: list[MappedComponent] = []
        side_results: list[ComponentCostResult] = []

        for component in gcp_components:
            mapped_service = str(component.cloud["gcp"])
            if is_gcp_ui_only_service(mapped_service):
                side_results.append(
                    build_ui_only_component_result(component, mapped_service)
                )
            elif is_gcp_service_fully_supported(mapped_service):
                supported_components.append(component)
            else:
                side_results.append(
                    build_unsupported_component_result(component, mapped_service)
                )

        inputs: list[ComponentPricingInput] = []
        if pricing_inputs is not None:
            supported_ids = {item.key for item in supported_components}
            inputs = [item for item in pricing_inputs if item.component_id in supported_ids]
        elif supported_components:
            inputs = self._usage_inference.infer_components(
                project,
                supported_components,
                feature_flags=feature_flags,
            )

        priced_result = ProjectGcpCostResult(
            components=[],
            total_usd=0.0,
            warnings=[],
            missing_prices=[],
            pool_summary={},
        )
        if inputs:
            quantity_result = calculate_project_gcp_sku_quantities(inputs)
            models_by_service: dict[str, GcpServicePricingModel] = {}
            for component_input in inputs:
                model = get_gcp_pricing_model(component_input.cloud_service)
                if model is not None:
                    models_by_service[model.service] = model
            priced_result = self._cost_calculator.calculate_project(
                quantity_result,
                models_by_service,
            )

        merged = self._merge_component_results(
            gcp_components,
            priced_result.components,
            side_results,
        )

        all_warnings = list(priced_result.warnings)
        for item in side_results:
            if item.pricing_status == "unsupported":
                all_warnings.append(
                    f"Component {item.component_id} ({item.catalog_service_name}): "
                    f"{item.unsupported_reason}"
                )
            elif item.pricing_status == "ui_only" and item.pricing_note:
                all_warnings.append(
                    f"Component {item.component_id} ({item.catalog_service_name}): "
                    f"{item.pricing_note}"
                )

        supported_count = sum(1 for item in merged if item.pricing_status == "supported")
        unsupported_count = sum(1 for item in merged if item.pricing_status == "unsupported")
        ui_only_count = sum(1 for item in merged if item.pricing_status == "ui_only")

        return ProjectGcpCostResult(
            components=merged,
            total_usd=round(
                sum(item.subtotal_usd for item in merged if item.pricing_status == "supported"),
                2,
            ),
            missing_prices=priced_result.missing_prices,
            warnings=all_warnings,
            pool_summary=priced_result.pool_summary,
            supported_component_count=supported_count,
            unsupported_component_count=unsupported_count,
            ui_only_component_count=ui_only_count,
        )

    @staticmethod
    def _merge_component_results(
        gcp_components: list[MappedComponent],
        priced_components: list[ComponentCostResult],
        unsupported_components: list[ComponentCostResult],
    ) -> list[ComponentCostResult]:
        by_id = {item.component_id: item for item in priced_components}
        by_id.update({item.component_id: item for item in unsupported_components})
        merged: list[ComponentCostResult] = []
        for component in gcp_components:
            if component.key not in by_id:
                continue
            merged.append(
                by_id[component.key].model_copy(update={"optional": component.optional})
            )
        return merged
