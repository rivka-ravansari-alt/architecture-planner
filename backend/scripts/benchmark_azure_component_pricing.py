"""Benchmark Azure component pricing for the self-esteem app scenario."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pricing.azure.benchmark import (
    AzureComponentPricingBenchmark,
    AzureComponentPricingBenchmarkFormatter,
)
from app.pricing.azure.verification import AzurePricingVerificationRunner
from app.pricing.catalog_factory import build_azure_cost_calculator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Azure component pricing across user counts."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of formatted tables.",
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
    benchmark = AzureComponentPricingBenchmark(runner)
    report = benchmark.run(inference_mode=args.inference)

    formatter = AzureComponentPricingBenchmarkFormatter()
    if args.json:
        print(formatter.format_json(report))
    else:
        print(formatter.format(report))


if __name__ == "__main__":
    main()
