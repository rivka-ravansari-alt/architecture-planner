"""Run the full Azure pricing pipeline and print a verification report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Project
from app.pricing.azure.verification import (
    AzurePricingReportFormatter,
    AzurePricingVerificationRunner,
)
from app.schemas.domain import MappedComponent
from app.pricing.catalog_factory import build_azure_cost_calculator


def sample_project() -> Project:
    return Project(
        name="TaskFlow",
        description="Sample SaaS architecture for Azure pricing verification",
        expected_users="1000",
        stage="mvp",
    )


def sample_components() -> list[MappedComponent]:
    return [
        MappedComponent(
            key="api",
            name="API",
            component_type="service",
            reason="HTTP API",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": "Functions"},
        ),
        MappedComponent(
            key="worker",
            name="Background Worker",
            component_type="worker",
            reason="Async jobs",
            category="core",
            optional=False,
            order=1,
            cloud={"aws": "ECS Fargate", "gcp": "Cloud Run", "azure": "Azure Container Apps"},
        ),
        MappedComponent(
            key="database",
            name="Primary Database",
            component_type="database",
            reason="Relational data",
            category="core",
            optional=False,
            order=2,
            cloud={"aws": "RDS PostgreSQL", "gcp": "Cloud SQL", "azure": "SQL Database"},
        ),
        MappedComponent(
            key="files",
            name="User Files",
            component_type="object_storage",
            reason="Uploads",
            category="core",
            optional=False,
            order=3,
            cloud={"aws": "S3", "gcp": "Cloud Storage", "azure": "Blob Storage"},
        ),
        MappedComponent(
            key="queue",
            name="Job Queue",
            component_type="queue",
            reason="Work distribution",
            category="core",
            optional=False,
            order=4,
            cloud={"aws": "SQS", "gcp": "Pub/Sub", "azure": "Service Bus"},
        ),
    ]


def sample_feature_flags() -> dict[str, bool]:
    return {
        "file_upload": True,
        "background_processing": True,
        "ai": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify full Azure pricing pipeline.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON report instead of formatted text.",
    )
    parser.add_argument(
        "--inference",
        choices=("llm", "heuristic"),
        default="heuristic",
        help="Usage assumption inference mode (default: heuristic).",
    )
    args = parser.parse_args()

    calculator = build_azure_cost_calculator()
    runner = AzurePricingVerificationRunner(calculator, inference_mode=args.inference)
    report = runner.run(
        sample_project(),
        sample_components(),
        feature_flags=sample_feature_flags(),
        inference_mode=args.inference,
    )

    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2))
    else:
        print(AzurePricingReportFormatter().format(report))


if __name__ == "__main__":
    main()
