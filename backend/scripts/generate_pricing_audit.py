"""Generate a complete pricing audit from live catalogs (read-only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.params import (
    AWS_CATALOG_SKIP_OPTIONS,
    AZURE_CATALOG_SKIP_OPTIONS,
    GCP_CATALOG_SKIP_OPTIONS,
)
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.schemas.domain import MappedComponent, RequirementContext
from app.services.pricing.catalog_lookup import PricingCatalogLookup
from app.services.pricing.component_models import build_component_model
from app.services.pricing.component_pricer import ComponentPricer
from app.services.pricing.formula_evaluator import FormulaEvaluator
from app.services.pricing.usage_profile import UsageProfileBuilder
from scripts.validate_pricing_scenarios import SCENARIOS

SKIP_BY_PROVIDER = {
    "aws": AWS_CATALOG_SKIP_OPTIONS,
    "gcp": GCP_CATALOG_SKIP_OPTIONS,
    "azure": AZURE_CATALOG_SKIP_OPTIONS,
}
PROVIDERS = ("aws", "gcp", "azure")


def _service_selection(component: MappedComponent, provider: str, lookup: PricingCatalogLookup) -> dict[str, Any]:
    options = component.cloud.get(provider, [])
    skip = SKIP_BY_PROVIDER.get(provider, frozenset())
    selected = lookup.pick_cloud_option(provider, options)
    rejected: list[dict[str, str]] = []
    for option in options:
        cleaned = str(option).strip()
        if not cleaned:
            rejected.append({"option": option, "reason": "empty option"})
        elif cleaned in skip:
            rejected.append({"option": cleaned, "reason": "listed in provider skip set (non-cloud / external)"})
        elif cleaned != selected:
            rejected.append({"option": cleaned, "reason": "not first billable option for this provider"})
    catalog_found = lookup.lookup(provider, selected) is not None if selected else False
    return {
        "architecture_options": options,
        "selected_service": selected,
        "catalog_found": catalog_found,
        "rejected_options": rejected,
        "selection_rule": (
            "The architecture maps one primary cloud service per provider. "
            "The estimator uses the first non-skipped option from that list."
        ),
    }


def _human_formula(formula: dict[str, str]) -> str:
    lines = []
    for key, expr in formula.items():
        if key == "total":
            continue
        label = key.replace("_", " ").title()
        lines.append(f"  {label} = {expr}")
    total = formula.get("total", "sum of terms")
    lines.append(f"  Total = {total}")
    return "\n".join(lines)


def _confidence_analysis(estimate, plan_notes: list[str], catalog_found: bool) -> dict[str, Any]:
    reasons: list[str] = []
    level = estimate.confidence

    if not catalog_found:
        reasons.append("No Firestore pricing catalog document matched this service.")
    if not estimate.matched_skus:
        reasons.append("No SKUs were selected for pricing.")
    if estimate.monthly_cost_min == 0 and estimate.monthly_cost_max == 0:
        reasons.append("Computed monthly cost is zero.")
    if all(sku.unit_price_usd <= 0 for sku in estimate.matched_skus) and estimate.matched_skus:
        reasons.append("All matched SKUs have zero unit price.")
    if any("fallback" in note.lower() for note in plan_notes + estimate.missing_data):
        reasons.append("Fallback pricing was used because the catalog lacked a suitable SKU.")
    if any("No priced" in note or "no_priced" in note for note in plan_notes + estimate.missing_data):
        reasons.append("Catalog matching did not find a confidently priced SKU for a required role.")
    if any("catalog:" in item for item in estimate.missing_data):
        reasons.append("Catalog document missing from Firestore.")
    if estimate.missing_data:
        reasons.append(f"Selection / default notes: {'; '.join(estimate.missing_data[:5])}")
    if level == "high" and reasons:
        reasons.append("Note: confidence flag may not reflect all caveats above.")

    fuzzy: list[str] = []
    for note in plan_notes + estimate.missing_data:
        lower = note.lower()
        if any(token in lower for token in ("fallback", "ignored", "no priced", "no suitable")):
            fuzzy.append(note)

    return {
        "level": level,
        "reasons": reasons or ["All required SKUs matched with priced catalog entries and no noted gaps."],
        "fuzzy_or_fallback_notes": fuzzy,
        "defaults_used": [n for n in estimate.missing_data if "default" in n.lower()],
    }


def _audit_component(
    *,
    component: MappedComponent,
    provider: str,
    expected_users: str,
    stage: str,
    requirements: RequirementContext,
    pricer: ComponentPricer,
    lookup: PricingCatalogLookup,
    evaluator: FormulaEvaluator,
    usage_builder: UsageProfileBuilder,
) -> dict[str, Any]:
    selection = _service_selection(component, provider, lookup)
    estimate = pricer.price_component(
        component=component,
        provider=provider,
        expected_users=expected_users,
        stage=stage,
        requirements=requirements,
    )

    plan = None
    formula_text = "N/A"
    usage_merged: dict[str, Any] = {}
    term_costs: dict[str, float] = {}

    if selection["selected_service"]:
        catalog = lookup.lookup(provider, selection["selected_service"])
        profile = usage_builder.build(
            component=component,
            expected_users=expected_users,
            stage=stage,
            requirements=requirements,
        )
        if catalog and estimate:
            plan = build_component_model(
                component_type=component.component_type,
                provider=provider,
                service_name=str(catalog.get("name", selection["selected_service"])),
                skus=catalog.get("skus", {}),
                profile=profile,
                stage=stage,
                expected_users=expected_users,
                requirements=requirements,
            )
            formula_text = _human_formula(plan.formula)
            usage_merged = dict(profile.values)
            usage_merged.update(plan.usage_overrides)
            if plan.skus and plan.formula:
                try:
                    _, term_costs = evaluator.evaluate_formula(
                        plan.formula,
                        usage=usage_merged,
                        skus=plan.skus,
                    )
                except Exception:
                    term_costs = {}

    sku_rows = []
    if estimate:
        for sku in estimate.matched_skus:
            sku_rows.append(
                {
                    "role": sku.role,
                    "sku_id": sku.sku_id,
                    "name": sku.description,
                    "unit_price_usd": sku.unit_price_usd,
                    "usage_unit": sku.usage_unit,
                    "quantity": sku.quantity,
                    "free_tier_applied": sku.free_tier_applied,
                    "cost_usd": sku.cost_usd,
                }
            )

    conf = _confidence_analysis(
        estimate,
        plan.selection_notes if plan else [],
        selection["catalog_found"],
    ) if estimate else {"level": "low", "reasons": ["No estimate produced."], "fuzzy_or_fallback_notes": [], "defaults_used": []}

    return {
        "component_key": component.key,
        "component_name": component.name,
        "component_type": component.component_type,
        "optional": component.optional,
        "service_selection": selection,
        "cloud_service": estimate.cloud_service if estimate else "N/A",
        "monthly_cost_min": estimate.monthly_cost_min if estimate else 0,
        "monthly_cost_max": estimate.monthly_cost_max if estimate else 0,
        "skus": sku_rows,
        "usage_assumptions": estimate.usage_assumptions if estimate else {},
        "usage_variables_merged": usage_merged,
        "formula": formula_text,
        "formula_raw": plan.formula if plan else {},
        "selection_notes": plan.selection_notes if plan else [],
        "term_costs": term_costs,
        "confidence": conf,
        "calculation_explanation": estimate.calculation_explanation if estimate else "",
    }


def _cross_provider_compare(component_key: str, audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_provider = {p: audits[p] for p in PROVIDERS if p in audits}
    costs = {p: (a["monthly_cost_min"], a["monthly_cost_max"]) for p, a in by_provider.items()}
    services = {p: a["cloud_service"] for p, a in by_provider.items()}

    min_costs = {p: c[0] for p, c in costs.items()}
    max_provider = max(min_costs, key=min_costs.get) if min_costs else None
    min_provider = min(min_costs, key=min_costs.get) if min_costs else None

    notes: list[str] = []
    spread = 0.0
    if min_costs:
        spread = max(min_costs.values()) - min(min_costs.values())
        notes.append(
            f"Nominal (low) cost spread across providers: ${spread:.2f}/month "
            f"({min_provider}=${min_costs[min_provider]:.2f} vs {max_provider}=${min_costs[max_provider]:.2f})."
        )

    # Flag likely model issues
    flags: list[str] = []
    for provider, audit in by_provider.items():
        conf = audit["confidence"]
        if conf["fuzzy_or_fallback_notes"]:
            flags.append(f"{provider.upper()}: fallback or weak catalog match")
        if audit["monthly_cost_min"] == 0 and audit["component_type"] not in ("payment",):
            if not audit["skus"]:
                flags.append(f"{provider.upper()}: $0 — likely missing catalog or SKUs")
        for sku in audit["skus"]:
            if sku["cost_usd"] > 500 and audit["component_type"] in ("api_gateway", "web_app", "queue"):
                flags.append(
                    f"{provider.upper()}: unusually high {sku['role']} cost (${sku['cost_usd']:.0f}) — verify SKU/unit"
                )

    equivalents = {
        "aws": services.get("aws", "N/A"),
        "gcp": services.get("gcp", "N/A"),
        "azure": services.get("azure", "N/A"),
    }
    notes.append(
        "Mapped equivalents: "
        + ", ".join(f"{p.upper()}={s}" for p, s in equivalents.items())
        + ". Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing."
    )

    return {
        "component_key": component_key,
        "costs_by_provider": costs,
        "services_by_provider": services,
        "analysis_notes": notes,
        "potential_issues": flags,
    }


def _format_cost_lines(audit: dict[str, Any]) -> str:
    lines = []
    if audit["term_costs"]:
        for term, cost in audit["term_costs"].items():
            label = term.replace("_", " ").title()
            lines.append(f"  {label:<22} ${cost:>10.2f}")
    elif audit["skus"]:
        for sku in audit["skus"]:
            label = sku["role"].replace("_", " ").title()
            lines.append(f"  {label:<22} ${sku['cost_usd']:>10.2f}")
    else:
        lines.append("  (no priced SKUs)")
    total = audit["monthly_cost_min"]
    lines.append(f"  {'Total':<22} ${total:>10.2f}  (range ${audit['monthly_cost_min']:.2f}–${audit['monthly_cost_max']:.2f})")
    return "\n".join(lines)


def _render_component_section(audit: dict[str, Any], provider: str) -> list[str]:
    lines = [
        f"#### {provider.upper()} — {audit['cloud_service']}",
        "",
        f"**Monthly estimate:** ${audit['monthly_cost_min']:.2f} – ${audit['monthly_cost_max']:.2f}",
        "",
        "**Service selection**",
        f"- Architecture options: `{audit['service_selection']['architecture_options']}`",
        f"- Selected: **{audit['service_selection']['selected_service']}**",
        f"- Catalog in Firestore: {'yes' if audit['service_selection']['catalog_found'] else 'no'}",
        f"- Rule: {audit['service_selection']['selection_rule']}",
    ]
    if audit["service_selection"]["rejected_options"]:
        lines.append("- Other options not used:")
        for item in audit["service_selection"]["rejected_options"]:
            lines.append(f"  - `{item['option']}`: {item['reason']}")
    lines.extend(["", "**Selected SKUs**", ""])
    if audit["skus"]:
        lines.append("| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |")
        lines.append("|------|--------|------|------------|------------|----------|-----------|------|")
        for s in audit["skus"]:
            free = f"{s['free_tier_applied']:g}" if s["free_tier_applied"] else "—"
            name = s["name"].replace("|", "/")[:60]
            lines.append(
                f"| {s['role']} | {s['sku_id']} | {name} | ${s['unit_price_usd']:.8f} | {s['usage_unit']} | {s['quantity']:g} | {free} | ${s['cost_usd']:.2f} |"
            )
    else:
        lines.append("_No SKUs matched._")
    if audit["selection_notes"]:
        lines.extend(["", "**SKU selection notes**", ""])
        for note in audit["selection_notes"]:
            lines.append(f"- {note}")

    uv = audit["usage_assumptions"].get("usage_variables", {})
    overrides = {k: v for k, v in audit.get("usage_variables_merged", {}).items() if k not in uv}
    lines.extend(["", "**Usage assumptions**", ""])
    base_keys = [
        "expected_users", "user_count", "stage", "requests_per_user_per_month",
        "request_share_for_component", "avg_request_duration_seconds", "cpu_vcpu",
        "memory_gib", "storage_per_user_gib",
    ]
    for key in base_keys:
        if key in audit["usage_assumptions"]:
            lines.append(f"- {key}: {audit['usage_assumptions'][key]}")
    lines.append("- Derived usage variables:")
    for key, val in sorted(uv.items()):
        lines.append(f"  - `{key}`: {val:g}")
    if overrides:
        lines.append("- Model overrides:")
        for key, val in sorted(overrides.items()):
            lines.append(f"  - `{key}`: {val:g}")

    lines.extend(["", "**Formula**", "", "```", audit["formula"], "```", "", "**Cost contribution**", "", "```", _format_cost_lines(audit), "```"])

    conf = audit["confidence"]
    lines.extend([
        "",
        f"**Confidence: {conf['level'].upper()}**",
        "",
    ])
    for reason in conf["reasons"]:
        lines.append(f"- {reason}")
    if conf["fuzzy_or_fallback_notes"]:
        lines.append("- Fuzzy / fallback matching:")
        for note in conf["fuzzy_or_fallback_notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    return lines


def generate_audit() -> tuple[dict[str, Any], str]:
    lookup = PricingCatalogLookup.from_firestore_client(FirestoreClientFactory.create())
    usage_builder = UsageProfileBuilder()
    evaluator = FormulaEvaluator()
    pricer = ComponentPricer(catalog_lookup=lookup, usage_builder=usage_builder, formula_evaluator=evaluator)

    report: dict[str, Any] = {"scenarios": []}
    md_lines = [
        "# Pricing Audit Report",
        "",
        "Read-only audit of the current SKU-based pricing pipeline. No pricing logic was modified.",
        "",
        "---",
        "",
    ]

    for scenario in SCENARIOS:
        scenario_entry: dict[str, Any] = {
            "name": scenario.name,
            "description": scenario.description,
            "expected_users": scenario.expected_users,
            "stage": scenario.stage,
            "requirements": scenario.requirements.__dict__,
            "components": [],
        }
        md_lines.extend([
            f"## Scenario: {scenario.name}",
            "",
            f"_{scenario.description}_",
            "",
            f"- Users: **{scenario.expected_users}** | Stage: **{scenario.stage}**",
            f"- Requirements: `{scenario.requirements.__dict__}`",
            "",
        ])

        for component in scenario.components:
            comp_audits: dict[str, Any] = {}
            for provider in PROVIDERS:
                comp_audits[provider] = _audit_component(
                    component=component,
                    provider=provider,
                    expected_users=scenario.expected_users,
                    stage=scenario.stage,
                    requirements=scenario.requirements,
                    pricer=pricer,
                    lookup=lookup,
                    evaluator=evaluator,
                    usage_builder=usage_builder,
                )

            comparison = _cross_provider_compare(component.key, comp_audits)
            scenario_entry["components"].append({
                "component": {
                    "key": component.key,
                    "name": component.name,
                    "type": component.component_type,
                },
                "providers": comp_audits,
                "cross_provider": comparison,
            })

            md_lines.extend([
                f"### Component: {component.name} (`{component.component_type}`)",
                "",
                "**Cross-provider comparison**",
                "",
            ])
            md_lines.append("| Provider | Service | Monthly (low–high) | Confidence |")
            md_lines.append("|----------|---------|-------------------|------------|")
            for p in PROVIDERS:
                a = comp_audits[p]
                md_lines.append(
                    f"| {p.upper()} | {a['cloud_service']} | ${a['monthly_cost_min']:.2f}–${a['monthly_cost_max']:.2f} | {a['confidence']['level']} |"
                )
            md_lines.append("")
            for note in comparison["analysis_notes"]:
                md_lines.append(f"- {note}")
            if comparison["potential_issues"]:
                md_lines.append("- **Potential issues to review:**")
                for flag in comparison["potential_issues"]:
                    md_lines.append(f"  - {flag}")
            md_lines.append("")

            for provider in PROVIDERS:
                md_lines.extend(_render_component_section(comp_audits[provider], provider))

            md_lines.append("---")
            md_lines.append("")

        report["scenarios"].append(scenario_entry)

    return report, "\n".join(md_lines)


def main() -> None:
    report, markdown = generate_audit()
    base = Path(__file__).parent.parent
    json_path = base / "pricing_audit.json"
    md_path = base / "PRICING_AUDIT.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
