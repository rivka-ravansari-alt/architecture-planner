"""Calculate monthly AWS costs from billable SKU quantities and catalog prices."""

from __future__ import annotations

from app.pricing.aws.catalog_lookup import AwsCatalogLookup
from app.pricing.aws.meter_scaling import AwsMeterUnitScaler
from app.pricing.aws.sku_roles import AwsSkuRoleResolver
from app.pricing.schemas import (
    AwsServicePricingModel,
    ComponentCostResult,
    ComponentSkuResult,
    MissingCatalogPrice,
    ProjectAwsCostResult,
    ProjectSkuQuantityResult,
    SkuCostLine,
)


class AwsCostCalculator:
    """Multiply billable SKU quantities by Firestore catalog unit prices."""

    def __init__(
        self,
        catalog_lookup: AwsCatalogLookup,
        role_resolver: AwsSkuRoleResolver,
        meter_scaler: AwsMeterUnitScaler,
    ) -> None:
        self._catalog_lookup = catalog_lookup
        self._role_resolver = role_resolver
        self._meter_scaler = meter_scaler

    def calculate_component(
        self,
        model: AwsServicePricingModel,
        adjusted: ComponentSkuResult,
    ) -> ComponentCostResult:
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
                pricing_status="partial",
                resolved_assumptions=adjusted.resolved,
                behavioral_assumptions=adjusted.behavioral_assumptions,
            )

        priced_sku_keys: set[str] = set()

        for quantity in adjusted.quantities:
            raw_qty = quantity.raw_quantity if quantity.raw_quantity is not None else quantity.quantity

            if raw_qty <= 0:
                continue

            if quantity.quantity <= 0:
                warnings.append(
                    f"SKU {quantity.sku_key!r}: {raw_qty:,.0f} {quantity.unit} calculated but "
                    f"$0 billable after free tier — included usage not shown as a cost line."
                )
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
                            reason=f"Catalog role {role!r} not found in aws_catalog.",
                        )
                    )
                    continue

                scaled = self._meter_scaler.scale(
                    quantity.quantity,
                    quantity.unit,
                    price.usage_unit,
                )
                if scaled is None:
                    missing_prices.append(
                        MissingCatalogPrice(
                            catalog_service_name=model.catalog_service_name,
                            sku_key=quantity.sku_key,
                            catalog_role=role,
                            reason=(
                                f"Cannot scale {quantity.quantity:,.0f} {quantity.unit!r} "
                                f"to catalog meter {price.usage_unit!r}."
                            ),
                        )
                    )
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
                priced_sku_keys.add(quantity.sku_key)
                break

            if not priced and roles:
                pass

        model_sku_keys = {sku.key for sku in model.pricing_model.calculated_skus}
        unpriced_with_billable_qty = {
            q.sku_key
            for q in adjusted.quantities
            if q.quantity > 0 and q.sku_key not in priced_sku_keys
        }
        if unpriced_with_billable_qty:
            warnings.append(
                "Billable SKU quantities calculated but not priced: "
                + ", ".join(sorted(unpriced_with_billable_qty))
            )

        missing_from_calculation = model_sku_keys - {
            q.sku_key for q in adjusted.quantities
        }
        if missing_from_calculation and adjusted.ready:
            warnings.append(
                "Pricing model SKUs not calculated: "
                + ", ".join(sorted(missing_from_calculation))
            )

        pricing_status = "supported"
        if missing_prices or unpriced_with_billable_qty:
            pricing_status = "partial"

        return ComponentCostResult(
            component_id=adjusted.component_id,
            service=adjusted.service,
            catalog_service_name=model.catalog_service_name,
            line_items=line_items,
            subtotal_usd=subtotal,
            missing_prices=missing_prices,
            warnings=warnings,
            ready=True,
            pricing_status=pricing_status,
            resolved_assumptions=adjusted.resolved,
            behavioral_assumptions=adjusted.behavioral_assumptions,
        )

    def calculate_project(
        self,
        project_result: ProjectSkuQuantityResult,
        models_by_service: dict[str, AwsServicePricingModel],
    ) -> ProjectAwsCostResult:
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
                        pricing_status="unsupported",
                        unsupported_reason=f"No pricing model registered for {component.service!r}.",
                        missing_implementation=["pricing_model_definition"],
                    )
                )
                continue

            result = self.calculate_component(model, component)
            components.append(result)
            total += result.subtotal_usd
            all_missing.extend(result.missing_prices)
            all_warnings.extend(result.warnings)

        return ProjectAwsCostResult(
            components=components,
            total_usd=total,
            missing_prices=all_missing,
            warnings=all_warnings,
            pool_summary=project_result.pool_summary,
        )
