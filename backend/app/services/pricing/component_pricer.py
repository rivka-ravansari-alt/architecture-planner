"""Calculate monthly cost for a single architecture component on one cloud provider."""

from __future__ import annotations

from typing import Any, Literal

from app.schemas.domain import ComponentCostEstimate, MappedComponent, MatchedSku, RequirementContext
from app.services.pricing.catalog_lookup import PricingCatalogLookup
from app.services.pricing.component_models import build_component_model
from app.services.pricing.formula_evaluator import FormulaEvaluationError, FormulaEvaluator
from app.services.pricing.profile_engine import populate_audit_usage_and_costs, term_cost_for_slot
from app.services.pricing.usage_profile import NON_BILLABLE_COMPONENT_TYPES, UsageProfileBuilder


class ComponentPricer:
    def __init__(
        self,
        *,
        catalog_lookup: PricingCatalogLookup,
        usage_builder: UsageProfileBuilder | None = None,
        formula_evaluator: FormulaEvaluator | None = None,
        profile_repository: Any | None = None,
        allow_profile_fallback: bool = False,
    ) -> None:
        self._catalog = catalog_lookup
        self._usage_builder = usage_builder or UsageProfileBuilder()
        self._evaluator = formula_evaluator or FormulaEvaluator()
        self._profile_repository = profile_repository
        self._allow_profile_fallback = allow_profile_fallback

    def price_component(
        self,
        *,
        component: MappedComponent,
        provider: str,
        expected_users: str,
        stage: str,
        requirements: RequirementContext,
    ) -> ComponentCostEstimate | None:
        if component.component_type in NON_BILLABLE_COMPONENT_TYPES:
            return None

        cloud_option = self._catalog.pick_cloud_option(provider, component.cloud.get(provider, []))
        if cloud_option is None:
            return ComponentCostEstimate(
                component_name=component.name,
                component_type=component.component_type,
                component_key=component.key,
                cloud_provider=provider,
                cloud_service="N/A",
                optional=component.optional,
                matched_skus=[],
                usage_assumptions={},
                monthly_cost_min=0.0,
                monthly_cost_max=0.0,
                calculation_explanation="No billable cloud service mapped for this provider.",
                confidence="low",
                missing_data=["cloud_service_option"],
            )

        catalog = self._catalog.lookup(provider, cloud_option)
        profile = self._usage_builder.build(
            component=component,
            expected_users=expected_users,
            stage=stage,
            requirements=requirements,
        )

        if catalog is None:
            return ComponentCostEstimate(
                component_name=component.name,
                component_type=component.component_type,
                component_key=component.key,
                cloud_provider=provider,
                cloud_service=cloud_option,
                optional=component.optional,
                matched_skus=[],
                usage_assumptions=self._public_assumptions(profile),
                monthly_cost_min=0.0,
                monthly_cost_max=0.0,
                calculation_explanation=(
                    f"No pricing catalog found for '{cloud_option}'. "
                    "Sync provider pricing data to Firestore before estimating."
                ),
                confidence="low",
                missing_data=[f"catalog:{provider}:{cloud_option}"],
            )

        raw_skus: dict[str, dict[str, Any]] = catalog.get("skus", {})
        service_name = str(catalog.get("name", cloud_option))

        plan = build_component_model(
            component_type=component.component_type,
            provider=provider,
            service_name=service_name,
            skus=raw_skus,
            profile=profile,
            stage=stage,
            expected_users=expected_users,
            requirements=requirements,
            profile_repository=self._profile_repository,
            allow_profile_fallback=self._allow_profile_fallback,
        )
        skus = plan.skus
        formula = plan.formula
        audit = plan.audit

        missing_data = list(profile.missing_defaults)
        resolution = plan.profile_resolution
        if resolution is not None:
            missing_data.extend(resolution.missing_data)
            if resolution.used_fallback:
                missing_data.append("fallback_pricing_profile")
        if resolution is not None and resolution.profile is None:
            return ComponentCostEstimate(
                component_name=component.name,
                component_type=component.component_type,
                component_key=component.key,
                cloud_provider=provider,
                cloud_service=service_name,
                optional=component.optional,
                matched_skus=[],
                usage_assumptions=self._public_assumptions(profile, plan.usage_overrides),
                monthly_cost_min=0.0,
                monthly_cost_max=0.0,
                calculation_explanation=(
                    f"No pricing profile found for '{service_name}' ({component.component_type}). "
                    "Seed pricing_component_profiles or explicitly enable fallback profiles."
                ),
                confidence="low",
                missing_data=missing_data,
                pricing_audit={
                    "profile": None,
                    "source": "missing",
                    "provider": provider,
                    "component_type": component.component_type,
                    "cloud_service": service_name,
                },
            )
        for role_value in audit.missing_required_roles:
            missing_data.append(f"missing_role:{role_value}")

        if not skus:
            missing_data.extend(plan.selection_notes)
            missing_data.append(f"no_priced_skus:{component.component_type}")
            pricing_audit = audit.to_dict() if audit else {}
            return ComponentCostEstimate(
                component_name=component.name,
                component_type=component.component_type,
                component_key=component.key,
                cloud_provider=provider,
                cloud_service=service_name,
                optional=component.optional,
                matched_skus=[],
                usage_assumptions=self._public_assumptions(profile, plan.usage_overrides),
                monthly_cost_min=0.0,
                monthly_cost_max=0.0,
                calculation_explanation=(
                    f"No suitable SKUs selected for '{service_name}' ({component.component_type}). "
                    + " ".join(plan.selection_notes)
                ),
                confidence="low",
                missing_data=missing_data,
                pricing_audit=pricing_audit,
            )

        low_profile = self._usage_builder.scale_profile(profile, 0.85)
        high_profile = self._usage_builder.scale_profile(profile, 1.15)
        low_usage = self._merge_usage(low_profile.values, plan.usage_overrides)
        high_usage = self._merge_usage(high_profile.values, plan.usage_overrides)
        nominal_usage = self._merge_usage(profile.values, plan.usage_overrides)

        try:
            low_total, low_terms = self._evaluator.evaluate_formula(
                formula,
                usage=self._apply_free_tiers(low_usage, skus),
                skus=skus,
            )
            high_total, _high_terms = self._evaluator.evaluate_formula(
                formula,
                usage=self._apply_free_tiers(high_usage, skus),
                skus=skus,
            )
        except FormulaEvaluationError as exc:
            return ComponentCostEstimate(
                component_name=component.name,
                component_type=component.component_type,
                component_key=component.key,
                cloud_provider=provider,
                cloud_service=service_name,
                optional=component.optional,
                matched_skus=[],
                usage_assumptions=self._public_assumptions(profile, plan.usage_overrides),
                monthly_cost_min=0.0,
                monthly_cost_max=0.0,
                calculation_explanation=f"Formula evaluation failed for '{service_name}': {exc}",
                confidence="low",
                missing_data=[f"formula_variables:{exc}", *missing_data, *plan.selection_notes],
                pricing_audit=audit.to_dict() if audit else {},
            )

        if audit is not None:
            populate_audit_usage_and_costs(
                audit,
                role_skus=plan.role_skus,
                usage=nominal_usage,
                term_costs=low_terms,
            )

        matched_skus = self._build_matched_skus(
            skus=skus,
            usage=nominal_usage,
            term_costs=low_terms,
        )
        realism = self._validate_price_realism(
            profile=plan.profile,
            low_total=low_total,
            high_total=high_total,
            expected_users=expected_users,
            stage=stage,
            missing_data=missing_data,
            matched_skus=matched_skus,
        )
        missing_data.extend(realism["missing_data"])
        confidence = self._confidence(
            matched_skus=matched_skus,
            missing_data=missing_data,
            low_total=low_total,
            high_total=high_total,
            selection_notes=plan.selection_notes,
        )

        explanation = self._build_explanation(
            service_name=service_name,
            profile=profile,
            usage_overrides=plan.usage_overrides,
            matched_skus=matched_skus,
            low_total=low_total,
            high_total=high_total,
            formula=formula,
            selection_notes=plan.selection_notes,
            audit=audit,
            price_realism=realism,
        )
        pricing_audit = audit.to_dict() if audit else {}
        if realism["scale_key"]:
            pricing_audit["price_realism"] = realism

        return ComponentCostEstimate(
            component_name=component.name,
            component_type=component.component_type,
            component_key=component.key,
            cloud_provider=provider,
            cloud_service=service_name,
            optional=component.optional,
            matched_skus=matched_skus,
            usage_assumptions=self._public_assumptions(profile, plan.usage_overrides),
            monthly_cost_min=round(low_total, 2),
            monthly_cost_max=round(max(low_total, high_total), 2),
            calculation_explanation=explanation,
            confidence=confidence,
            missing_data=missing_data,
            pricing_audit=pricing_audit,
        )

    def _build_matched_skus(
        self,
        *,
        skus: dict[str, dict[str, Any]],
        usage: dict[str, float],
        term_costs: dict[str, float],
    ) -> list[MatchedSku]:
        matched: list[MatchedSku] = []
        for role, sku in skus.items():
            quantity = self._evaluator.quantity_for_role(role, usage, sku)
            billable, free_applied = self._evaluator.billable_quantity(quantity, sku)
            cost = term_cost_for_slot(role, term_costs)
            if cost is None:
                unit_price = float(sku.get("unit_price_usd", 0.0))
                cost = billable * unit_price

            matched.append(
                MatchedSku(
                    role=role,
                    sku_id=str(sku.get("sku_id", role)),
                    description=str(sku.get("description", role)),
                    usage_unit=str(sku.get("usage_unit", "")),
                    unit_price_usd=float(sku.get("unit_price_usd", 0.0)),
                    quantity=round(quantity, 4),
                    free_tier_applied=round(free_applied, 4),
                    cost_usd=round(max(0.0, cost), 4),
                )
            )
        return matched

    @staticmethod
    def _merge_usage(
        base: dict[str, float],
        overrides: dict[str, float],
    ) -> dict[str, float]:
        merged = dict(base)
        merged.update(overrides)
        return merged

    def _apply_free_tiers(
        self,
        usage: dict[str, float],
        skus: dict[str, dict[str, Any]],
    ) -> dict[str, float]:
        from app.services.pricing.usage_profile import ROLE_USAGE_VARIABLE

        adjusted = dict(usage)
        for role, sku in skus.items():
            variable = ROLE_USAGE_VARIABLE.get(role, role)
            if variable in adjusted:
                billable, _ = self._evaluator.billable_quantity(adjusted[variable], sku)
                adjusted[variable] = billable
            elif role in adjusted:
                billable, _ = self._evaluator.billable_quantity(adjusted[role], sku)
                adjusted[role] = billable
        return adjusted

    @staticmethod
    def _public_assumptions(
        profile,
        usage_overrides: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        usage_variables = {key: round(value, 4) for key, value in profile.values.items()}
        if usage_overrides:
            usage_variables.update({key: round(value, 4) for key, value in usage_overrides.items()})
        return {
            **profile.assumptions,
            "usage_variables": usage_variables,
        }

    @staticmethod
    def _confidence(
        *,
        matched_skus: list[MatchedSku],
        missing_data: list[str],
        low_total: float,
        high_total: float,
        selection_notes: list[str],
    ) -> Literal["high", "medium", "low"]:
        if not matched_skus:
            return "low"
        if low_total == 0.0 and high_total == 0.0:
            return "low"
        if all(sku.unit_price_usd <= 0.0 for sku in matched_skus):
            return "low"
        if any("fallback" in note.lower() for note in selection_notes):
            return "low"
        if any("No priced" in note or "no_priced" in note for note in missing_data):
            return "low"
        if any("catalog:" in item or "formula_variables:" in item for item in missing_data):
            return "low"
        if any(item.startswith("price_outlier:") for item in missing_data):
            return "low"
        if "missing_pricing_profile" in missing_data or "fallback_pricing_profile" in missing_data:
            return "low"
        if any(item.startswith("missing_role:") for item in missing_data):
            return "low"
        if missing_data:
            return "medium"
        return "high"

    @staticmethod
    def _build_explanation(
        *,
        service_name: str,
        profile,
        usage_overrides: dict[str, float],
        matched_skus: list[MatchedSku],
        low_total: float,
        high_total: float,
        formula: dict[str, str],
        selection_notes: list[str],
        audit,
        price_realism: dict[str, Any] | None = None,
    ) -> str:
        users = profile.assumptions.get("user_count", "?")
        stage = profile.assumptions.get("stage", "?")
        parts = [
            f"Estimated {service_name} cost for ~{users} users ({stage}) "
            f"at ${low_total:.2f}-${high_total:.2f}/month."
        ]

        if audit is not None:
            parts.append(f"Profile '{audit.profile_name}' ({audit.formula}).")

        if matched_skus:
            sku_bits = []
            for sku in matched_skus:
                bit = (
                    f"{sku.role}: {sku.quantity:g} {sku.usage_unit or 'units'} "
                    f"@ ${sku.unit_price_usd:.8f} = ${sku.cost_usd:.2f}"
                )
                if sku.free_tier_applied:
                    bit += f" (free tier: {sku.free_tier_applied:g})"
                sku_bits.append(bit)
            parts.append("SKU breakdown: " + "; ".join(sku_bits) + ".")

        if audit is not None and audit.role_costs:
            role_cost_bits = [
                f"{role}=${cost:.2f}" for role, cost in sorted(audit.role_costs.items())
            ]
            parts.append("Cost by role: " + ", ".join(role_cost_bits) + ".")

        if usage_overrides:
            override_bits = [f"{key}={value:g}" for key, value in usage_overrides.items()]
            parts.append("Model overrides: " + ", ".join(override_bits) + ".")

        if selection_notes:
            parts.append("Selection: " + "; ".join(selection_notes) + ".")

        if price_realism and price_realism.get("reasons"):
            parts.append("Realism validation: " + "; ".join(price_realism["reasons"]) + ".")

        if profile.missing_defaults:
            parts.append("Defaults: " + "; ".join(profile.missing_defaults) + ".")

        if formula.get("total"):
            parts.append(f"Formula: {formula['total']}.")

        return " ".join(parts)

    @staticmethod
    def _validate_price_realism(
        *,
        profile: Any | None,
        low_total: float,
        high_total: float,
        expected_users: str,
        stage: str,
        missing_data: list[str],
        matched_skus: list[MatchedSku],
    ) -> dict[str, Any]:
        if profile is None:
            return {"scale_key": "", "missing_data": [], "reasons": []}

        scale_key = ComponentPricer._scale_key(expected_users, stage)
        ranges = getattr(profile, "expected_monthly_ranges", {}) or {}
        expected = ranges.get(scale_key)
        if not expected:
            return {"scale_key": scale_key, "missing_data": [], "reasons": []}

        expected_min = float(expected.get("min", 0.0))
        expected_max = float(expected.get("max", 0.0))
        notes: list[str] = []
        missing: list[str] = []
        missing_roles = [item.split(":", 1)[1] for item in missing_data if item.startswith("missing_role:")]
        all_zero_skus = matched_skus and all(sku.unit_price_usd <= 0.0 for sku in matched_skus)

        if expected_max > 0 and high_total > expected_max * 3:
            missing.append(f"price_outlier:high:{scale_key}")
            notes.append(
                f"${high_total:.2f}/month is far above expected {scale_key} range "
                f"(${expected_min:.2f}-${expected_max:.2f})."
            )
        elif expected_max > 0 and high_total > expected_max:
            missing.append(f"price_warning:high:{scale_key}")
            notes.append(
                f"${high_total:.2f}/month is above expected {scale_key} range "
                f"(${expected_min:.2f}-${expected_max:.2f})."
            )

        if high_total == 0.0 and (expected_min > 0.0 or missing_roles):
            missing.append(f"price_outlier:low:{scale_key}")
            reason = "Estimate is $0 for a component expected to have non-zero monthly cost"
            if missing_roles:
                reason += f" and is missing role(s): {', '.join(missing_roles)}"
            notes.append(reason + ".")
        elif expected_min > 0.0 and high_total < expected_min / 3 and missing_roles:
            missing.append(f"price_outlier:low:{scale_key}")
            notes.append(
                f"${high_total:.2f}/month is far below expected {scale_key} range "
                f"(${expected_min:.2f}-${expected_max:.2f}) with missing role(s): "
                f"{', '.join(missing_roles)}."
            )
        elif all_zero_skus and expected_min > 0.0:
            missing.append(f"price_warning:low:{scale_key}")
            notes.append("All selected SKUs are zero-priced for a component expected to have paid usage.")

        return {
            "scale_key": scale_key,
            "expected_min": expected_min,
            "expected_max": expected_max,
            "actual_low": round(low_total, 2),
            "actual_high": round(max(low_total, high_total), 2),
            "missing_data": missing,
            "reasons": notes,
        }

    @staticmethod
    def _scale_key(expected_users: str, stage: str) -> str:
        try:
            users = int(str(expected_users).replace(",", ""))
        except ValueError:
            users = 1_000

        if stage == "production" or users >= 10_000:
            return "production_10000"
        if users <= 100:
            return "mvp_100"
        return "mvp_1000"
