"""End-to-end AWS catalog pricing for a project."""

from __future__ import annotations

from app.models import Project
from app.pricing.aws.cost_calculator import AwsCostCalculator
from app.pricing.aws.coverage import is_aws_service_fully_supported, unsupported_reason_for_service
from app.pricing.aws.project_pricing import calculate_project_aws_sku_quantities
from app.pricing.aws.registry import get_aws_pricing_model, normalize_aws_service_name
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.pricing.schemas import (
    AwsServicePricingModel,
    ComponentCostResult,
    ComponentPricingInput,
    ProjectAwsCostResult,
)
from app.schemas.domain import MappedComponent


def _aws_mapped_components(components: list[MappedComponent]) -> list[MappedComponent]:
    return [
        component
        for component in sorted(components, key=lambda item: item.order)
        if component.cloud.get("aws")
    ]


def build_unsupported_component_result(
    component: MappedComponent,
    mapped_service: str,
) -> ComponentCostResult:
    """Build an explicit unsupported pricing result — never silent $0."""
    reason, missing = unsupported_reason_for_service(mapped_service)
    canonical = normalize_aws_service_name(mapped_service)
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


class AwsProjectCostingPipeline:
    """End-to-end AWS catalog pricing for a project."""

    def __init__(
        self,
        usage_inference: AwsUsageInferenceEngine,
        cost_calculator: AwsCostCalculator,
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
    ) -> ProjectAwsCostResult:
        aws_components = _aws_mapped_components(components)
        if not aws_components:
            return ProjectAwsCostResult(
                total_usd=0.0,
                warnings=["No AWS-mapped components found for catalog pricing."],
            )

        supported_components: list[MappedComponent] = []
        unsupported_results: list[ComponentCostResult] = []

        for component in aws_components:
            mapped_service = str(component.cloud["aws"])
            if is_aws_service_fully_supported(mapped_service):
                supported_components.append(component)
            else:
                unsupported_results.append(
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

        priced_result = ProjectAwsCostResult(
            components=[],
            total_usd=0.0,
            warnings=[],
            missing_prices=[],
            pool_summary={},
        )
        if inputs:
            quantity_result = calculate_project_aws_sku_quantities(inputs)
            models_by_service: dict[str, AwsServicePricingModel] = {}
            for component_input in inputs:
                model = get_aws_pricing_model(component_input.cloud_service)
                if model is not None:
                    models_by_service[model.service] = model
            priced_result = self._cost_calculator.calculate_project(
                quantity_result,
                models_by_service,
            )

        merged = self._merge_component_results(
            aws_components,
            priced_result.components,
            unsupported_results,
        )

        all_warnings = list(priced_result.warnings)
        for item in unsupported_results:
            all_warnings.append(
                f"Component {item.component_id} ({item.catalog_service_name}): {item.unsupported_reason}"
            )

        supported_count = sum(1 for item in merged if item.pricing_status == "supported")
        unsupported_count = sum(1 for item in merged if item.pricing_status == "unsupported")

        return ProjectAwsCostResult(
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
        )

    @staticmethod
    def _merge_component_results(
        aws_components: list[MappedComponent],
        priced_components: list[ComponentCostResult],
        unsupported_components: list[ComponentCostResult],
    ) -> list[ComponentCostResult]:
        by_id = {item.component_id: item for item in priced_components}
        by_id.update({item.component_id: item for item in unsupported_components})
        merged: list[ComponentCostResult] = []
        for component in aws_components:
            if component.key not in by_id:
                continue
            merged.append(
                by_id[component.key].model_copy(update={"optional": component.optional})
            )
        return merged
