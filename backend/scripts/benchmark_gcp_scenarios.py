"""Benchmark GCP catalog pricing for five benchmark scenarios with usage inference."""



from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path



sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



from app.clients.ai_client import AIClientFactory

from app.pricing.gcp.benchmark import (

    GcpScenarioPricingBenchmark,

    GcpScenarioPricingBenchmarkFormatter,

    GcpScenarioPricingBenchmarkReport,

    build_usage_service,

)

from app.pricing.gcp.project_costing import GcpProjectCostingPipeline

from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine

from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS

from app.pricing.catalog_factory import build_gcp_cost_calculator





def run_benchmark(*, inference_mode: str = "llm", users: int | None = None) -> dict:

    calculator = build_gcp_cost_calculator()

    pipeline = GcpProjectCostingPipeline(GcpUsageInferenceEngine(), calculator)

    ai_client = None if inference_mode == "heuristic" else AIClientFactory.create()

    usage_service = build_usage_service(ai_client=ai_client, inference_mode=inference_mode)  # type: ignore[arg-type]

    benchmark = GcpScenarioPricingBenchmark(

        pipeline,

        usage_service,

        inference_mode=inference_mode,  # type: ignore[arg-type]

        user_counts=(users,) if users is not None else BENCHMARK_USER_COUNTS,

    )

    report = benchmark.run()

    return GcpScenarioPricingBenchmarkFormatter.to_serializable(report)





def main() -> None:

    parser = argparse.ArgumentParser(description="GCP benchmark for five pricing scenarios.")

    parser.add_argument(

        "--mode",

        choices=("llm", "heuristic"),

        default="llm",

        help="Usage inference mode (default: llm).",

    )

    parser.add_argument(

        "--users",

        type=int,

        default=None,

        help="Run only this user count (default: all benchmark counts).",

    )

    parser.add_argument(

        "--json",

        action="store_true",

        help="Print JSON only (no formatted tables).",

    )

    args = parser.parse_args()



    report_dict = run_benchmark(inference_mode=args.mode, users=args.users)

    if args.json:

        print(json.dumps(report_dict, indent=2))

        return



    report = GcpScenarioPricingBenchmarkReport.model_validate(report_dict)

    print(GcpScenarioPricingBenchmarkFormatter.format_full_report(report))





if __name__ == "__main__":

    main()

