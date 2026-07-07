"""Calculate monthly Azure costs from billable SKU quantities and catalog prices."""

from __future__ import annotations

from app.pricing.azure.catalog_lookup import AzureCatalogLookup
from app.pricing.azure.meter_scaling import MeterUnitScaler
from app.pricing.azure.sku_roles import SkuRoleResolver
from app.pricing.schemas import (
    AzureServicePricingModel,
    ComponentCostResult,
    ComponentSkuResult,
    MissingCatalogPrice,
    ProjectAzureCostResult,
    ProjectSkuQuantityResult,
    SkuCostLine,
)


class AzureCostCalculator:
    """Multiply billable SKU quantities by Firestore catalog unit prices."""

    def __init__(
        self,
        catalog_lookup: AzureCatalogLookup,
        role_resolver: SkuRoleResolver,
        meter_scaler: MeterUnitScaler,
    ) -> None:
        self._catalog_lookup = catalog_lookup
        self._role_resolver = role_resolver
        self._meter_scaler = meter_scaler

    def calculate_component(
        self,
        model: AzureServicePricingModel,
        adjusted: ComponentSkuResult,
    ) -> ComponentCostResult:
        """Price one component's billable SKU quantities."""
        line_items: list[SkuCostLine] = []
        missing_prices: list[MissingCatalogPrice] = []
        warnings: list[str] = list(adjusted.warnings)
        subtotal = 0.0

        if not adjusted.ready:
            return ComponentCostResult(
                component_id=adjusted.component_id,
                service=adjusted.service,
                catalog_service_name=model.catalog_service_name,
                line_items=[],
                subtotal_usd=0.0,
                missing_prices=[],
                warnings=warnings + ["Component SKU quantities not ready for pricing."],
                ready=False,
                resolved_assumptions=adjusted.resolved,
                behavioral_assumptions=adjusted.behavioral_assumptions,
            )

        for quantity in adjusted.quantities:
            if quantity.quantity <= 0:
                continue

            roles = self._role_resolver.resolve(model, quantity.sku_key)
            if not roles:
                if self._role_resolver.is_unpriced_sku(model, quantity.sku_key):
                    warnings.append(
                        f"SKU {quantity.sku_key!r} has no catalog role mapping (v1 skip)."
                    )
                else:
                    missing_prices.append(
                        MissingCatalogPrice(
                            catalog_service_name=model.catalog_service_name,
                            sku_key=quantity.sku_key,
                            catalog_role=None,
                            reason="No catalog role mapping for sku_key.",
                        )
                    )
                continue

            priced = False
            for role in roles:
                price = self._catalog_lookup.get_unit_price(
                    model.catalog_service_name,
                    role,
                    resolved=adjusted.resolved,
                )
                if price is None:
                    missing_prices.append(
                        MissingCatalogPrice(
                            catalog_service_name=model.catalog_service_name,
                            sku_key=quantity.sku_key,
                            catalog_role=role,
                            reason=f"Catalog role {role!r} not found in azure_catalog.",
                        )
                    )
                    continue

                scaled = self._meter_scaler.scale(
                    quantity.quantity,
                    quantity.unit,
                    price.usage_unit,
                )
                if scaled is None:
                    warnings.append(
                        f"Cannot scale {quantity.sku_key!r} "
                        f"({quantity.unit}) to catalog meter {price.usage_unit!r}."
                    )
                    continue

                billable_units, formula_note = scaled
                monthly_cost = billable_units * price.unit_price_usd
                line_items.append(
                    SkuCostLine(
                        sku_key=quantity.sku_key,
                        catalog_role=role,
                        quantity=quantity.quantity,
                        unit=quantity.unit,
                        billable_units=billable_units,
                        unit_price_usd=price.unit_price_usd,
                        usage_unit=price.usage_unit,
                        monthly_cost_usd=monthly_cost,
                        free_tier_applied=quantity.free_tier_applied,
                        formula_note=formula_note,
                    )
                )
                subtotal += monthly_cost
                priced = True
                break

            if not priced and roles:
                pass  # missing_prices already populated

        return ComponentCostResult(
            component_id=adjusted.component_id,
            service=adjusted.service,
            catalog_service_name=model.catalog_service_name,
            line_items=line_items,
            subtotal_usd=subtotal,
            missing_prices=missing_prices,
            warnings=warnings,
            ready=True,
            resolved_assumptions=adjusted.resolved,
            behavioral_assumptions=adjusted.behavioral_assumptions,
        )

    def calculate_project(
        self,
        project_result: ProjectSkuQuantityResult,
        models_by_service: dict[str, AzureServicePricingModel],
    ) -> ProjectAzureCostResult:
        """Price all components in a project SKU quantity result."""
        components: list[ComponentCostResult] = []
        all_missing: list[MissingCatalogPrice] = []
        all_warnings: list[str] = []
        total = 0.0

        for component in project_result.components:
            model = models_by_service.get(component.service)
            if model is None:
                components.append(
                    ComponentCostResult(
                        component_id=component.component_id,
                        service=component.service,
                        catalog_service_name=component.service,
                        subtotal_usd=0.0,
                        warnings=[f"Unknown pricing model for {component.service!r}."],
                        ready=False,
                    )
                )
                continue

            result = self.calculate_component(model, component)
            components.append(result)
            total += result.subtotal_usd
            all_missing.extend(result.missing_prices)
            all_warnings.extend(result.warnings)

        return ProjectAzureCostResult(
            components=components,
            total_usd=total,
            missing_prices=all_missing,
            warnings=all_warnings,
            pool_summary=project_result.pool_summary,
        )
