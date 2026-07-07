"""End-to-end pricing pipeline audit for Azure, AWS, and GCP."""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Project
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.project_pricing import calculate_project_aws_sku_quantities
from app.pricing.azure.project_costing import AzureProjectCostingPipeline
from app.pricing.azure.project_pricing import calculate_project_azure_sku_quantities
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.gcp.project_pricing import calculate_project_gcp_sku_quantities
from app.pricing.usage.service import UsageAssumptionsService
from app.services.component_mapper_service import ComponentMapperService
from app.services.project_pricing_service import ProjectPricingService
from app.services.catalog_service import CatalogService
from app.core.database import SessionLocal
from app.pricing.catalog_factory import (
    build_aws_cost_calculator,
    build_azure_cost_calculator,
    build_gcp_cost_calculator,
)

PROJECT_ID = "91a67ae9-1691-40a2-bb17-d37b11317f33"

PROVIDERS = ("azure", "aws", "gcp")


@dataclass
class StageResult:
    name: str
    status: str  # executed | missing | warning
    detail: str = ""


@dataclass
class ProviderAudit:
    provider: str
    stages: list[StageResult] = field(default_factory=list)
    component_costs: list[dict] = field(default_factory=list)
    total_usd: float = 0.0
    warnings: list[str] = field(default_factory=list)


def _load_project() -> tuple[Project, list, dict | None, list]:
    conn = sqlite3.connect("architecture_planner.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (PROJECT_ID,))
    row = dict(cur.fetchone())
    project = Project(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        stage=row["stage"],
        expected_users=row["expected_users"],
        workflow_status=row["workflow_status"],
    )
    cur.execute(
        """
        SELECT pc.*, cm.aws, cm.gcp, cm.azure
        FROM project_components pc
        LEFT JOIN cloud_mappings cm ON cm.component_id = pc.id
        WHERE pc.project_id = ?
        ORDER BY pc."order"
        """,
        (PROJECT_ID,),
    )
    db_components = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM requirement_answers WHERE project_id = ?", (PROJECT_ID,))
    ans_row = cur.fetchone()
    answers = None
    if ans_row:
        row_dict = dict(ans_row)
        answers = {
            k: row_dict[k]
            for k in ("auth", "file_upload", "background_processing", "dashboards", "ai", "payments", "include_edge_cases")
            if k in row_dict
        }
    cur.execute(
        "SELECT provider, monthly_low, notes, pricing_detail FROM cost_estimates WHERE project_id = ?",
        (PROJECT_ID,),
    )
    stored_costs = {r["provider"]: dict(r) for r in cur.fetchall()}
    conn.close()
    return project, db_components, answers, stored_costs


def _build_pricing_service(db) -> ProjectPricingService:
    catalog = CatalogService(db)
    mapper = ComponentMapperService(catalog)
    azure_calc = build_azure_cost_calculator()
    aws_calc = build_aws_cost_calculator()
    gcp_calc = build_gcp_cost_calculator()
    return ProjectPricingService(
        AzureProjectCostingPipeline(
            __import__("app.pricing.azure.usage_inference", fromlist=["AzureUsageInferenceEngine"]).AzureUsageInferenceEngine(),
            azure_calc,
        ),
        AwsProjectCostingPipeline(
            __import__("app.pricing.aws.usage_inference", fromlist=["AwsUsageInferenceEngine"]).AwsUsageInferenceEngine(),
            aws_calc,
        ),
        GcpProjectCostingPipeline(
            __import__("app.pricing.gcp.usage_inference", fromlist=["GcpUsageInferenceEngine"]).GcpUsageInferenceEngine(),
            gcp_calc,
        ),
        __import__("app.pricing.providers.heuristic", fromlist=["HeuristicProviderPricing"]).HeuristicProviderPricing(mapper=mapper),
    )


def _format_assumptions(pricing_inputs: list) -> list[str]:
    lines: list[str] = []
    for comp in pricing_inputs:
        lines.append(f"  [{comp.component_id}] service={comp.cloud_service}")
        for a in comp.resolved:
            lines.append(
                f"    {a.key}={a.value} | source={a.source.value} | "
                f"confidence={a.confidence.value} | {a.reasoning[:120]}"
            )
        missing = getattr(comp, "missing", None)
        if missing:
            for m in missing:
                lines.append(f"    MISSING: {m.key} — {m.description}")
    return lines


def _format_skus(quantity_result) -> list[str]:
    lines: list[str] = []
    for comp in quantity_result.components:
        lines.append(f"  [{comp.component_id}] service={comp.service} ready={comp.ready}")
        for q in comp.quantities:
            raw = q.raw_quantity if q.raw_quantity is not None else q.quantity
            ft = f" free_tier_deducted={q.free_tier_deducted}" if q.free_tier_deducted else ""
            lines.append(
                f"    {q.sku_key}: raw={raw} billable={q.quantity} {q.unit}{ft}"
            )
            lines.append(f"      formula: {q.formula}")
            if q.input_values_used:
                lines.append(f"      inputs: {json.dumps(q.input_values_used)}")
        for m in comp.missing:
            lines.append(f"    MISSING ASSUMPTION: {m.key}")
    return lines


def _format_catalog_costs(pipeline_result) -> list[str]:
    lines: list[str] = []
    for comp in pipeline_result.components:
        lines.append(
            f"  [{comp.component_id}] {comp.catalog_service_name} "
            f"status={comp.pricing_status} subtotal=${comp.subtotal_usd:.4f}"
        )
        for line in comp.line_items:
            lines.append(
                f"    catalog role={line.catalog_role} sku_key={line.sku_key} "
                f"unit={line.usage_unit} price=${line.unit_price_usd}"
            )
            lines.append(
                f"      {line.billable_units} x ${line.unit_price_usd} = ${line.monthly_cost_usd:.4f}"
            )
        for mp in comp.missing_prices:
            lines.append(f"    MISSING CATALOG: {mp.sku_key} — {mp.reason}")
        for w in comp.warnings:
            lines.append(f"    WARNING: {w}")
    return lines


def audit_provider(
    provider: str,
    project: Project,
    mapped_components,
    mapper: ComponentMapperService,
    pricing_inputs,
    inference_source: str,
    pipeline_result,
    quantity_result,
) -> ProviderAudit:
    audit = ProviderAudit(provider=provider)
    feature_flags = mapper.feature_flags_from_components(mapped_components)

    # Stage 1 - product input (shared, marked on first provider only)
    audit.stages.append(StageResult("1. Product Input", "executed", "Loaded from DB"))

    # Stage 2 - architecture
    comp_count = len(mapped_components)
    audit.stages.append(
        StageResult(
            "2. Architecture Generation",
            "executed" if comp_count else "missing",
            f"{comp_count} logical components persisted (LLM step ran earlier in workflow)",
        )
    )

    # Stage 3 - cloud mapping
    mapped = [c for c in mapped_components if c.cloud.get(provider)]
    if mapped:
        lines = [f"{c.key} -> {c.cloud.get(provider)}" for c in mapped]
        audit.stages.append(
            StageResult("3. Cloud Service Mapping", "executed", "; ".join(lines))
        )
    else:
        audit.stages.append(StageResult("3. Cloud Service Mapping", "missing", "No mappings"))

    # Stage 4 - usage assumptions
    assumption_lines = _format_assumptions(pricing_inputs) if pricing_inputs else []
    missing = []
    for comp in pricing_inputs or []:
        for m in getattr(comp, "missing", []) or []:
            missing.append(f"{comp.component_id}/{m.key}")
    status = "warning" if missing else "executed"
    audit.stages.append(
        StageResult(
            "4. Usage Assumptions",
            status,
            f"inference_source={inference_source}; {len(pricing_inputs or [])} components"
            + (f"; missing={missing}" if missing else "")
            + "\n" + "\n".join(assumption_lines[:40])
            + ("..." if len(assumption_lines) > 40 else ""),
        )
    )

    # Stage 5 - validation
    if inference_source == "llm":
        val_status = "executed"
        val_detail = "LLMUsageAssumptionsResponseValidator ran during generate_pricing"
    elif inference_source in ("heuristic_only", "heuristic_fallback"):
        val_status = "warning"
        val_detail = (
            "LLM validation skipped; heuristic provider resolves against pricing model required_inputs"
        )
    else:
        val_status = "warning"
        val_detail = f"Unknown inference source: {inference_source}"
    if provider in ("aws", "gcp") and inference_source == "llm":
        val_status = "warning"
        val_detail += " | AWS/GCP always re-infer heuristically even when Azure uses LLM"
    audit.stages.append(StageResult("5. Validation", val_status, val_detail))

    # Stage 6 - SKU quantities
    sku_lines = _format_skus(quantity_result)
    not_ready = [c.component_id for c in quantity_result.components if not c.ready]
    status = "warning" if not_ready else "executed"
    audit.stages.append(
        StageResult(
            "6. SKU Quantity Calculation",
            status,
            f"{sum(len(c.quantities) for c in quantity_result.components)} SKU lines"
            + (f"; not_ready={not_ready}" if not_ready else "")
            + "\n" + "\n".join(sku_lines),
        )
    )

    # Stage 7 - free tier
    ft_applied = any(q.free_tier_deducted > 0 for c in quantity_result.components for q in c.quantities)
    pool = quantity_result.pool_summary
    audit.stages.append(
        StageResult(
            "7. Free Tier / Included Usage",
            "executed" if ft_applied or pool else "warning",
            f"free_tier_deducted={ft_applied}; pool_summary={json.dumps(pool)[:200]}",
        )
    )

    # Stage 8 & 9 - catalog + cost (from pipeline result)
    cost_lines = _format_catalog_costs(pipeline_result)
    missing_cat = [
        f"{mp.catalog_service_name}/{mp.sku_key}: {mp.reason}"
        for comp in pipeline_result.components
        for mp in comp.missing_prices
    ]
    cat_status = "warning" if missing_cat else "executed"
    audit.stages.append(
        StageResult(
            "8. Catalog Lookup",
            cat_status,
            f"{sum(len(c.line_items) for c in pipeline_result.components)} priced; "
            f"{len(missing_cat)} missing"
            + (f"\n    missing: {missing_cat}" if missing_cat else "")
            + "\n" + "\n".join(cost_lines),
        )
    )
    cost_status = "warning" if missing_cat else "executed"
    silent_zero = [
        c.component_id
        for c in pipeline_result.components
        if c.ready and not c.line_items and c.subtotal_usd == 0 and c.pricing_status == "supported"
    ]
    if silent_zero:
        cost_status = "warning"
    audit.stages.append(
        StageResult(
            "9. Cost Calculation",
            cost_status,
            (f"silent_zero_components={silent_zero}" if silent_zero else "All billable SKUs priced")
            + "\n" + "\n".join(cost_lines),
        )
    )

    # Stage 10 - component cost
    for comp in pipeline_result.components:
        audit.component_costs.append(
            {
                "component_id": comp.component_id,
                "service": comp.catalog_service_name,
                "status": comp.pricing_status,
                "subtotal_usd": round(comp.subtotal_usd, 4),
            }
        )
    audit.stages.append(
        StageResult(
            "10. Component Cost",
            "executed",
            "; ".join(
                f"{c['component_id']}=${c['subtotal_usd']}" for c in audit.component_costs
            ),
        )
    )

    audit.total_usd = pipeline_result.total_usd
    audit.warnings = list(pipeline_result.warnings)
    audit.stages.append(
        StageResult("11. Project Cost", "executed", f"${pipeline_result.total_usd:.2f}/mo")
    )
    return audit


def main() -> None:
    project, db_components, answers, stored_costs = _load_project()
    db = SessionLocal()
    try:
        catalog = CatalogService(db)
        mapper = ComponentMapperService(catalog)
        from app.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(db)
        full_project = repo.find_by_id(PROJECT_ID)
        if full_project is None:
            raise SystemExit(f"Project {PROJECT_ID} not found in database")
        mapped = mapper.map_components_from_db(full_project.components)
        feature_flags = mapper.feature_flags_from_components(mapped)

        usage_service = UsageAssumptionsService(inference_mode="heuristic")
        azure_inputs = usage_service.infer_components(
            project, mapped, provider="azure", feature_flags=feature_flags, inference_mode="heuristic"
        )
        aws_inputs = usage_service.infer_components(
            project, mapped, provider="aws", feature_flags=feature_flags, inference_mode="heuristic"
        )
        gcp_inputs = usage_service.infer_components(
            project, mapped, provider="gcp", feature_flags=feature_flags, inference_mode="heuristic"
        )

        pricing_service = _build_pricing_service(db)
        costs = pricing_service.estimate(
            project,
            mapped,
            mapper=mapper,
            pricing_inputs=azure_inputs,
            aws_pricing_inputs=aws_inputs,
            gcp_pricing_inputs=gcp_inputs,
            inference_source="heuristic_only",
            aws_inference_source="heuristic_only",
            gcp_inference_source="heuristic_only",
        )

        azure_qty = calculate_project_azure_sku_quantities(azure_inputs)
        aws_qty = calculate_project_aws_sku_quantities(aws_inputs)
        gcp_qty = calculate_project_gcp_sku_quantities(gcp_inputs)

        azure_pipeline = pricing_service._azure_pipeline.calculate(
            project, mapped, pricing_inputs=azure_inputs, feature_flags=feature_flags
        )
        aws_pipeline = pricing_service._aws_pipeline.calculate(
            project, mapped, pricing_inputs=aws_inputs, feature_flags=feature_flags
        )
        gcp_pipeline = pricing_service._gcp_pipeline.calculate(
            project, mapped, pricing_inputs=gcp_inputs, feature_flags=feature_flags
        )

        audits = [
            audit_provider("azure", project, mapped, mapper, azure_inputs, "heuristic_only", azure_pipeline, azure_qty),
            audit_provider("aws", project, mapped, mapper, aws_inputs, "heuristic_only", aws_pipeline, aws_qty),
            audit_provider("gcp", project, mapped, mapper, gcp_inputs, "heuristic_only", gcp_pipeline, gcp_qty),
        ]
    finally:
        db.close()

    lines: list[str] = []
    lines.append("=" * 100)
    lines.append("PRICING PIPELINE AUDIT — Sarika Self-Esteem (100 users, MVP)")
    lines.append("=" * 100)
    lines.append("")
    lines.append("## 1. Product Input")
    lines.append(f"  Name: {project.name}")
    lines.append(f"  Description: {project.description[:120]}...")
    lines.append(f"  Expected users: {project.expected_users}")
    lines.append(f"  Stage: {project.stage}")
    if answers:
        lines.append(
            f"  Requirements: auth={answers['auth']}, file_upload={answers['file_upload']}, "
            f"ai={answers['ai']}, background_processing={answers['background_processing']}, "
            f"dashboards={answers['dashboards']}, payments={answers['payments']}"
        )
    lines.append("  Status: ✅ Executed")
    lines.append("")

    lines.append("## 2. Architecture Generation")
    lines.append(f"  Components ({len(db_components)}):")
    for c in db_components:
        lines.append(f"    - {c['key']}: {c['name']} [{c['component_type']}] optional={bool(c['optional'])}")
    lines.append("  Status: ✅ Executed (components persisted from prior generate-components step)")
    lines.append("")

    for audit in audits:
        lines.append("")
        lines.append("#" * 80)
        lines.append(f"# {audit.provider.upper()} PIPELINE")
        lines.append("#" * 80)
        for stage in audit.stages:
            icon = {"executed": "✅", "missing": "❌", "warning": "⚠️"}.get(stage.status, "?")
            lines.append(f"{icon} {stage.name}")
            if stage.detail:
                for part in stage.detail.split("\n"):
                    lines.append(f"    {part}")
        cost = next(c for c in costs if c.provider == audit.provider)
        lines.append(f"\n  Persisted DB notes format: {'legacy JSON' if (stored_costs.get(audit.provider, {}).get('notes') or '').startswith('{') else 'catalog text'}")
        lines.append(f"  pricing_detail in DB: {'null (legacy)' if stored_costs.get(audit.provider, {}).get('pricing_detail') is None else 'present'}")
        lines.append(f"  Live catalog estimate: ${cost.monthly_low:.2f}/mo")

    lines.append("")
    lines.append("=" * 100)
    lines.append("## 12. Cloud Comparison (Frontend)")
    lines.append("  deriveArchitecture.js uses API cost_estimates when present (source=catalog)")
    lines.append("  computeHeuristicCosts() ONLY when cost_estimates is empty")
    lines.append("  Status: ✅ Catalog-based when pricing generated; ⚠️ heuristic fallback if no pricing")
    lines.append("")

    lines.append("=" * 100)
    lines.append("MASTER CHECKLIST")
    lines.append("=" * 100)
    stage_names = [
        "1. Product Input",
        "2. Architecture Generation",
        "3. Cloud Service Mapping",
        "4. Usage Assumptions",
        "5. Validation",
        "6. SKU Quantity Calculation",
        "7. Free Tier / Included Usage",
        "8. Catalog Lookup",
        "9. Cost Calculation",
        "10. Component Cost",
        "11. Project Cost",
        "12. Cloud Comparison",
    ]
    header = f"{'Stage':<35}" + "".join(f"{p.upper():>10}" for p in PROVIDERS)
    lines.append(header)
    lines.append("-" * len(header))
    for name in stage_names:
        row = f"{name:<35}"
        if name == "12. Cloud Comparison":
            row += f"{'✅':>10}{'✅':>10}{'✅':>10}"
        else:
            for audit in audits:
                stage = next((s for s in audit.stages if s.name == name), None)
                icon = {"executed": "✅", "missing": "❌", "warning": "⚠️"}.get(stage.status if stage else "missing", "?")
                row += f"{icon:>10}"
        lines.append(row)

    lines.append("")
    lines.append("LEGACY / DIVERGENT CODE PATHS STILL PRESENT")
    lines.append("-" * 50)
    legacy = [
        ("CostEstimatorService", "backend/app/services/cost_estimator_service.py", "NOT wired to generate_pricing; README only"),
        ("HeuristicProviderPricing.estimate_provider", "backend/app/pricing/providers/heuristic.py", "Injected but NEVER called by ProjectPricingService.estimate()"),
        ("Frontend computeHeuristicCosts", "frontend/.../deriveArchitecture.js", "Active ONLY when cost_estimates[] is empty"),
        ("DB notes JSON (component_costs)", "cost_estimates.notes", "Legacy format from removed formula engine; pricing_detail should be used"),
        ("Catalog formula linear engine", "pricing_ingestion/data/*_formulas.py", "Ingestion-time only; NOT used at runtime by catalog pipelines"),
        ("AWS/GCP heuristic-only usage when Azure uses LLM", "generation_service._infer_usage_assumptions", "Asymmetric: Azure LLM, AWS/GCP forced heuristic"),
    ]
    for name, path, note in legacy:
        lines.append(f"  • {name}")
        lines.append(f"      {path}")
        lines.append(f"      {note}")

    lines.append("")
    lines.append("PROVIDER PIPELINE ARCHITECTURE DIFFERENCES")
    lines.append("-" * 50)
    diffs = [
        "Azure: all mapped components priced; no unsupported/ui_only gates",
        "AWS: unsupported services explicitly flagged (coverage.py); no ui_only concept",
        "GCP: unsupported + ui_only ($0) component handling; GcpCatalogMeterSelector",
        "Azure: AzureCatalogMeterSelector for tier/storage class SKU selection",
        "AWS: direct catalog role lookup (no meter selector class)",
        "Usage inference: per-provider UsageModelBuilder (azure/aws/gcp) via HeuristicFallbackProvider",
        "All three: shared UsageAssumptionsService facade, same ComponentPricingInput schema",
        "All three: project_pricing -> free_tier -> cost_calculator -> project_costing pattern",
    ]
    for d in diffs:
        lines.append(f"  • {d}")

    report = "\n".join(lines)
    out = Path(__file__).parent / "pricing_pipeline_audit_report.txt"
    out.write_text(report, encoding="utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(report)
    print(f"\nReport saved to {out}")


if __name__ == "__main__":
    main()
