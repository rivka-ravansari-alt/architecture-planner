"""Benchmark five AWS platform scenarios with random MAU and extended services."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.ai_client import AIClientFactory
from app.pricing.aws.benchmark import build_usage_service
from app.pricing.aws.platform_benchmark import (
    AwsPlatformScenarioBenchmark,
    AwsPlatformScenarioBenchmarkFormatter,
)
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.pricing.catalog_factory import build_aws_cost_calculator


def run_benchmark(*, inference_mode: str = "heuristic", seed: int = 42) -> dict:
    calculator = build_aws_cost_calculator()
    pipeline = AwsProjectCostingPipeline(AwsUsageInferenceEngine(), calculator)
    ai_client = None if inference_mode == "heuristic" else AIClientFactory.create()
    usage_service = build_usage_service(ai_client=ai_client, inference_mode=inference_mode)  # type: ignore[arg-type]
    benchmark = AwsPlatformScenarioBenchmark(
        pipeline,
        usage_service,
        inference_mode=inference_mode,  # type: ignore[arg-type]
        random_seed=seed,
    )
    report = benchmark.run()
    return AwsPlatformScenarioBenchmarkFormatter.to_serializable(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AWS platform benchmark: 5 scenarios, random MAU, extended services.",
    )
    parser.add_argument(
        "--mode",
        choices=("llm", "heuristic"),
        default="heuristic",
        help="Usage inference mode (default: heuristic).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for user-count assignment (default: 42).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON only (no formatted tables).",
    )
    parser.add_argument(
        "--table-only",
        action="store_true",
        help="Print only the App Name / Users / Service / Price table.",
    )
    args = parser.parse_args()

    report_dict = run_benchmark(inference_mode=args.mode, seed=args.seed)
    if args.json:
        print(json.dumps(report_dict, indent=2))
        return

    from app.pricing.aws.platform_benchmark import AwsPlatformScenarioBenchmarkReport

    report = AwsPlatformScenarioBenchmarkReport.model_validate(report_dict)
    if args.table_only:
        print(AwsPlatformScenarioBenchmarkFormatter.format_service_price_table(report))
    else:
        print(AwsPlatformScenarioBenchmarkFormatter.format_full_report(report))


if __name__ == "__main__":
    main()
