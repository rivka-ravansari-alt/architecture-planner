"""Multi-component AWS SKU quantity orchestration with shared free-tier pools."""

from __future__ import annotations

from app.pricing.aws.free_tier import FreeTierPoolState, apply_project_free_tier
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.aws.sku_quantities import calculate_aws_sku_quantities
from app.pricing.schemas import (
    ComponentPricingInput,
    ComponentSkuResult,
    ProjectSkuQuantityResult,
)


def calculate_project_aws_sku_quantities(
    components: list[ComponentPricingInput],
) -> ProjectSkuQuantityResult:
    """Calculate billable SKU quantities for all components with shared free-tier pooling."""
    pool_state = FreeTierPoolState()
    results: list[ComponentSkuResult] = []

    for component in sorted(components, key=lambda item: item.order):
        model = get_aws_pricing_model(component.cloud_service)
        if model is None:
            results.append(
                ComponentSkuResult(
                    component_id=component.component_id,
                    service=component.cloud_service,
                    quantities=[],
                    included_usage=[],
                    missing=[],
                    ready=False,
                    warnings=[f"Unknown AWS service {component.cloud_service!r}."],
                )
            )
            continue

        raw = calculate_aws_sku_quantities(model, component.resolved)
        adjusted = apply_project_free_tier(
            model,
            raw,
            pool_state,
            resolved=component.resolved,
        )
        results.append(
            ComponentSkuResult(
                component_id=component.component_id,
                service=adjusted.service,
                quantities=adjusted.quantities,
                included_usage=adjusted.included_usage,
                missing=adjusted.missing,
                ready=adjusted.ready,
                resolved=component.resolved,
                behavioral_assumptions=component.behavioral_assumptions,
                warnings=adjusted.warnings,
            )
        )

    return ProjectSkuQuantityResult(
        components=results,
        pool_summary=pool_state.summary(),
    )
