"""Run realistic pricing scenarios against live Firestore catalogs."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.params import COMPONENT_CATEGORY_CORE, COMPONENT_CATEGORY_OPTIONAL
from app.schemas.domain import MappedComponent, RequirementContext
from app.services.cost_estimator_service import CostEstimatorService


def _comp(
    key: str,
    name: str,
    component_type: str,
    *,
    aws: list[str],
    gcp: list[str],
    azure: list[str],
    optional: bool = False,
) -> MappedComponent:
    category = COMPONENT_CATEGORY_OPTIONAL if optional else COMPONENT_CATEGORY_CORE
    return MappedComponent(
        key=key,
        name=name,
        component_type=component_type,
        reason=f"{name} for the product.",
        category=category,
        optional=optional,
        order=0,
        cloud={"aws": aws, "gcp": gcp, "azure": azure},
        implementation_options={},
    )


@dataclass
class Scenario:
    name: str
    description: str
    expected_users: str
    stage: str
    requirements: RequirementContext
    components: list[MappedComponent] = field(default_factory=list)


SCENARIOS: list[Scenario] = [
    Scenario(
        name="TaskFlow",
        description="Small team task manager, MVP, ~100 users",
        expected_users="100",
        stage="mvp",
        requirements=RequirementContext(auth=True, file_upload=True),
        components=[
            _comp("client_web", "Web Client", "web_app", aws=["Amplify Hosting"], gcp=["Firebase Hosting"], azure=["Azure App Service"]),
            _comp("api_layer", "API Gateway", "api_gateway", aws=["API Gateway"], gcp=["API Gateway"], azure=["API Management"]),
            _comp("app_service", "Backend API", "app_service", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
            _comp("auth", "Authentication", "auth", aws=["Cognito"], gcp=["Firebase Authentication"], azure=["Entra ID B2C"]),
            _comp("database", "Database", "database", aws=["DynamoDB"], gcp=["Cloud Firestore"], azure=["Azure Cosmos DB"]),
            _comp("object_storage", "File Storage", "object_storage", aws=["S3"], gcp=["Cloud Storage"], azure=["Blob Storage"], optional=True),
        ],
    ),
    Scenario(
        name="ShopLite",
        description="E-commerce storefront, MVP, ~1,000 users, uploads + payments",
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(auth=True, file_upload=True, payments=True),
        components=[
            _comp("client_web", "Storefront", "web_app", aws=["Amplify Hosting"], gcp=["Firebase Hosting"], azure=["Azure App Service"]),
            _comp("cdn", "CDN", "cdn", aws=["CloudFront"], gcp=["Networking"], azure=["Content Delivery Network"]),
            _comp("api_layer", "API Gateway", "api_gateway", aws=["API Gateway"], gcp=["API Gateway"], azure=["API Management"]),
            _comp("app_service", "Order Service", "app_service", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
            _comp("database", "Product DB", "database", aws=["RDS"], gcp=["Cloud SQL"], azure=["SQL Database"]),
            _comp("object_storage", "Product Images", "object_storage", aws=["S3"], gcp=["Cloud Storage"], azure=["Blob Storage"]),
            _comp("payments", "Payments", "payment", aws=["Stripe"], gcp=["Stripe"], azure=["Stripe"]),
        ],
    ),
    Scenario(
        name="InsightAI",
        description="AI document assistant, MVP, ~1,000 users with AI + background jobs",
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(auth=True, file_upload=True, ai=True, background_processing=True),
        components=[
            _comp("client_web", "Web App", "web_app", aws=["Amplify Hosting"], gcp=["Firebase Hosting"], azure=["Azure App Service"]),
            _comp("api_layer", "API Gateway", "api_gateway", aws=["API Gateway"], gcp=["API Gateway"], azure=["API Management"]),
            _comp("app_service", "API Service", "app_service", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
            _comp("queue_worker", "Job Worker", "queue_worker", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
            _comp("queue", "Message Queue", "queue", aws=["SQS"], gcp=["Cloud Pub/Sub"], azure=["Service Bus"]),
            _comp("object_storage", "Document Storage", "object_storage", aws=["S3"], gcp=["Cloud Storage"], azure=["Blob Storage"]),
            _comp("ai_service", "AI Inference", "ai_provider", aws=["Bedrock"], gcp=["Vertex AI"], azure=["Foundry Models"]),
            _comp("database", "Metadata DB", "database", aws=["DynamoDB"], gcp=["Cloud Firestore"], azure=["Azure Cosmos DB"]),
        ],
    ),
    Scenario(
        name="HealthPortal",
        description="Healthcare patient portal, production scale, ~10,000 users",
        expected_users="10000",
        stage="production",
        requirements=RequirementContext(auth=True, file_upload=True, dashboards=True),
        components=[
            _comp("client_web", "Patient Portal", "web_app", aws=["Amplify Hosting"], gcp=["Firebase Hosting"], azure=["Azure App Service"]),
            _comp("load_balancer", "Load Balancer", "load_balancer", aws=["Application Load Balancer"], gcp=["Networking"], azure=["Application Gateway"]),
            _comp("api_layer", "API Gateway", "api_gateway", aws=["API Gateway"], gcp=["API Gateway"], azure=["API Management"]),
            _comp("app_service", "Core API", "app_service", aws=["ECS Fargate"], gcp=["Cloud Run"], azure=["Azure Container Apps"]),
            _comp("auth", "Identity", "auth", aws=["Cognito"], gcp=["Identity Platform"], azure=["Entra ID B2C"]),
            _comp("database", "Patient Records", "database", aws=["RDS"], gcp=["Cloud SQL"], azure=["SQL Database"]),
            _comp("object_storage", "Medical Files", "object_storage", aws=["S3"], gcp=["Cloud Storage"], azure=["Blob Storage"]),
            _comp("monitoring", "Monitoring", "monitoring", aws=["CloudWatch"], gcp=["Cloud Monitoring"], azure=["Azure Monitor"]),
        ],
    ),
    Scenario(
        name="SocialFeed",
        description="Mobile social feed, MVP, ~10,000 users, heavy media",
        expected_users="10000",
        stage="mvp",
        requirements=RequirementContext(auth=True, file_upload=True, background_processing=True),
        components=[
            _comp("client_mobile", "Mobile App", "mobile_app", aws=["Amplify"], gcp=["Firebase"], azure=["Azure App Center"]),
            _comp("cdn", "Media CDN", "cdn", aws=["CloudFront"], gcp=["Networking"], azure=["Content Delivery Network"]),
            _comp("api_layer", "API Gateway", "api_gateway", aws=["API Gateway"], gcp=["API Gateway"], azure=["API Management"]),
            _comp("app_service", "Feed API", "app_service", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
            _comp("cache", "Feed Cache", "cache", aws=["ElastiCache"], gcp=["Cloud Memorystore for Redis"], azure=["Redis Cache"]),
            _comp("database", "User Data", "database", aws=["DynamoDB"], gcp=["Cloud Firestore"], azure=["Azure Cosmos DB"]),
            _comp("object_storage", "Media Storage", "object_storage", aws=["S3"], gcp=["Cloud Storage"], azure=["Blob Storage"]),
            _comp("queue_worker", "Media Processor", "queue_worker", aws=["Lambda"], gcp=["Cloud Run"], azure=["Functions"]),
        ],
    ),
]


def _serialize_scenario(scenario: Scenario) -> dict:
    return {
        "name": scenario.name,
        "description": scenario.description,
        "requirements": {
            "expected_users": scenario.expected_users,
            "stage": scenario.stage,
            **scenario.requirements.__dict__,
        },
        "components": [
            {
                "key": c.key,
                "name": c.name,
                "type": c.component_type,
                "optional": c.optional,
                "cloud": c.cloud,
            }
            for c in scenario.components
        ],
    }


def _serialize_estimate(provider_cost) -> dict:
    return {
        "provider": provider_cost.provider,
        "monthly_low": provider_cost.monthly_low,
        "monthly_high": provider_cost.monthly_high,
        "components": [
            {
                "component_name": c.component_name,
                "component_type": c.component_type,
                "cloud_service": c.cloud_service,
                "monthly_cost_min": c.monthly_cost_min,
                "monthly_cost_max": c.monthly_cost_max,
                "confidence": c.confidence,
                "missing_data": c.missing_data,
                "usage_assumptions": c.usage_assumptions,
                "matched_skus": [
                    {
                        "role": s.role,
                        "sku_id": s.sku_id,
                        "description": s.description,
                        "usage_unit": s.usage_unit,
                        "unit_price_usd": s.unit_price_usd,
                        "quantity": s.quantity,
                        "cost_usd": s.cost_usd,
                    }
                    for s in c.matched_skus
                ],
                "calculation_explanation": c.calculation_explanation,
            }
            for c in provider_cost.component_costs
        ],
    }


def main() -> None:
    estimator = CostEstimatorService()
    results: list[dict] = []

    for scenario in SCENARIOS:
        estimates = estimator.estimate(
            components=scenario.components,
            expected_users=scenario.expected_users,
            stage=scenario.stage,
            requirements=scenario.requirements,
        )
        results.append(
            {
                "scenario": _serialize_scenario(scenario),
                "estimates": [_serialize_estimate(e) for e in estimates],
            }
        )

    out_path = Path(__file__).parent.parent / "validation_pricing_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
