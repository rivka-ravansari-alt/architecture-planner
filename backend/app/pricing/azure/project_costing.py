"""Orchestrate Azure usage inference, SKU quantities, free tier, and catalog costing."""

from __future__ import annotations

from app.models import Project
from app.pricing.azure.cost_calculator import AzureCostCalculator
from app.pricing.azure.project_pricing import calculate_project_azure_sku_quantities
from app.pricing.azure.registry import get_azure_pricing_model
from app.pricing.azure.usage_inference import AzureUsageInferenceEngine
from app.pricing.schemas import AzureServicePricingModel, ComponentPricingInput, ProjectAzureCostResult
from app.schemas.domain import MappedComponent


class AzureProjectCostingPipeline:
    """End-to-end Azure catalog pricing for a project."""

    def __init__(
        self,
        usage_inference: AzureUsageInferenceEngine,
        cost_calculator: AzureCostCalculator,
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
    ) -> ProjectAzureCostResult:
        """Infer usage (unless provided), compute quantities, and price from catalog."""
        inputs = pricing_inputs or self._usage_inference.infer_components(
            project,
            components,
            feature_flags=feature_flags,
        )
        if not inputs:
            return ProjectAzureCostResult(
                total_usd=0.0,
                warnings=["No Azure-mapped components found for catalog pricing."],
            )

        quantity_result = calculate_project_azure_sku_quantities(inputs)
        models_by_service: dict[str, AzureServicePricingModel] = {}
        for component_input in inputs:
            model = get_azure_pricing_model(component_input.azure_service)
            if model is not None:
                models_by_service[model.service] = model

        priced = self._cost_calculator.calculate_project(quantity_result, models_by_service)
        optional_by_id = {component.key: component.optional for component in components}
        enriched_components = [
            item.model_copy(
                update={"optional": optional_by_id.get(item.component_id, False)}
            )
            for item in priced.components
        ]
        return priced.model_copy(update={"components": enriched_components})
