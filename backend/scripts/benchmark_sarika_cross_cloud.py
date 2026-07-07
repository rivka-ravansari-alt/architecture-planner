"""Cross-cloud monthly cost benchmark for Sarika Self-Esteem at multiple user scales."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.ai_client import AIClientFactory
from app.config.params import COST_CURRENCY
from app.core.database import SessionLocal
from app.models import Project
from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS, USER_COUNT_TO_PROJECT_LABEL
from app.pricing.usage.service import UsageAssumptionsService
from app.repositories.project_repository import ProjectRepository
from app.services.component_mapper_service import ComponentMapperService
from app.services.catalog_service import CatalogService
from app.pricing.catalog_factory import build_project_pricing_service
from app.services.project_pricing_service import ProjectPricingService

PROJECT_ID = "91a67ae9-1691-40a2-bb17-d37b11317f33"
PRODUCT_DESCRIPTION = (
    "A self-esteem improvement application that provides users with daily exercises "
    "designed to build confidence, positive self-image, and emotional well-being. "
    "Users can complete exercises, track their progress, maintain daily streaks, and "
    "receive personalized recommendations. The system stores user progress and provides "
    "a simple dashboard to visualize growth over time."
)


def _build_pricing_service(db, mapper: ComponentMapperService) -> ProjectPricingService:
    del db
    return build_project_pricing_service(mapper)


def _infer_provider_inputs(
    usage_service: UsageAssumptionsService,
    project: Project,
    components,
    feature_flags: dict,
    *,
    shared_raw: str | None,
) -> tuple[dict, str]:
    """Return provider inputs and top-level inference label."""
    if shared_raw:
        try:
            shared = usage_service.parse_shared_response(
                shared_raw,
                project,
                components,
                feature_flags=feature_flags,
            )
            mapped = usage_service.map_shared_to_providers(
                shared,
                project=project,
                components=components,
                feature_flags=feature_flags,
            )
            sources = {p: mapped[p].inference_source for p in mapped}
            label = "llm" if all(s == "llm" for s in sources.values()) else "mixed"
            return mapped, label
        except Exception:
            pass
    fallback = usage_service.infer_all_providers_heuristic(
        project,
        components,
        feature_flags=feature_flags,
        inference_source="heuristic_fallback",
    )
    return fallback, "heuristic"


def run_benchmark(*, use_llm: bool = True) -> dict:
    db = SessionLocal()
    try:
        repo = ProjectRepository(db)
        catalog = CatalogService(db)
        mapper = ComponentMapperService(catalog)
        pricing = _build_pricing_service(db, mapper)

        project = repo.find_by_id(PROJECT_ID)
        if project is None:
            raise SystemExit(f"Project {PROJECT_ID} not found in database")

        components = mapper.map_components_from_db(project.components)
        feature_flags = mapper.feature_flags_from_components(components)

        usage_service = UsageAssumptionsService(
            ai_client=AIClientFactory.create() if use_llm else None
        )

        shared_raw: str | None = None
        shared_parsed = False
        inference_mode = "heuristic"
        if use_llm:
            try:
                prompt = usage_service.build_shared_prompt(
                    project,
                    components,
                    feature_flags=feature_flags,
                )
                shared_raw = AIClientFactory.create().generate(prompt)
                # Validate once before reusing across user tiers.
                usage_service.parse_shared_response(
                    shared_raw,
                    project,
                    components,
                    feature_flags=feature_flags,
                )
                shared_parsed = True
                inference_mode = "shared_llm"
            except Exception:
                shared_raw = None
                shared_parsed = False
                inference_mode = "heuristic"

        rows: list[dict] = []
        for users in BENCHMARK_USER_COUNTS:
            tier_project = Project(
                id=project.id,
                name=project.name,
                description=project.description or PRODUCT_DESCRIPTION,
                stage=project.stage or "mvp",
                expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
                architecture_summary=project.architecture_summary or "",
            )
            tier_project.answers = project.answers

            provider_inputs, source_label = _infer_provider_inputs(
                usage_service,
                tier_project,
                components,
                feature_flags,
                shared_raw=shared_raw if shared_parsed else None,
            )

            costs = pricing.estimate(
                tier_project,
                components,
                mapper=mapper,
                pricing_inputs=list(provider_inputs["azure"].components),
                aws_pricing_inputs=list(provider_inputs["aws"].components),
                gcp_pricing_inputs=list(provider_inputs["gcp"].components),
                inference_source=provider_inputs["azure"].inference_source,
                aws_inference_source=provider_inputs["aws"].inference_source,
                gcp_inference_source=provider_inputs["gcp"].inference_source,
            )
            by_provider = {c.provider: c for c in costs}
            rows.append(
                {
                    "users": users,
                    "azure_usd": round(by_provider["azure"].monthly_low, 2),
                    "aws_usd": round(by_provider["aws"].monthly_low, 2),
                    "gcp_usd": round(by_provider["gcp"].monthly_low, 2),
                    "inference": {
                        "azure": provider_inputs["azure"].inference_source,
                        "aws": provider_inputs["aws"].inference_source,
                        "gcp": provider_inputs["gcp"].inference_source,
                    },
                }
            )

        return {
            "product": project.name,
            "description": project.description or PRODUCT_DESCRIPTION,
            "stage": project.stage,
            "components": len(components),
            "inference_mode": inference_mode,
            "currency": COST_CURRENCY,
            "catalog": "firestore",
            "rows": rows,
        }
    finally:
        db.close()


def _print_table(report: dict) -> None:
    print()
    print(f"## {report['product']} — Cross-Cloud Monthly Cost")
    print()
    print(report["description"][:200] + "...")
    print()
    print(f"Stage: {report['stage']} | Components: {report['components']} | Inference: {report['inference_mode']} | Catalog: {report['catalog']}")
    print()
    print("| Users | Azure (USD/mo) | AWS (USD/mo) | Google Cloud (USD/mo) |")
    print("|------:|---------------:|-------------:|----------------------:|")
    for row in report["rows"]:
        print(
            f"| {row['users']:,} | ${row['azure_usd']:,.2f} | ${row['aws_usd']:,.2f} | ${row['gcp_usd']:,.2f} |"
        )
    print()


if __name__ == "__main__":
    report = run_benchmark(use_llm=True)
    _print_table(report)
    out = Path(__file__).parent / "sarika_cross_cloud_benchmark.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved: {out}")
