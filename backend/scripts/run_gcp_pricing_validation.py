"""Run the full GCP pricing validation suite and write benchmark reports."""



from __future__ import annotations



import argparse

import sys

from datetime import UTC, datetime

from pathlib import Path



sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



from app.pricing.azure.scenarios import ALL_BENCHMARK_SCENARIOS, SCENARIOS_BY_ID

from app.pricing.gcp.project_costing import GcpProjectCostingPipeline

from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine

from app.pricing.gcp.validation_suite import (

    GcpPricingValidationSuite,

    GcpPricingValidationSuiteFormatter,

)

from app.pricing.catalog_factory import build_gcp_cost_calculator



REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "pricing-validation" / "reports"





def main() -> int:

    parser = argparse.ArgumentParser(

        description="Run GCP pricing validation benchmarks across application scenarios."

    )

    parser.add_argument(

        "--json",

        action="store_true",

        help="Print structured JSON to stdout instead of summary text.",

    )

    parser.add_argument(

        "--inference",

        choices=("llm", "heuristic"),

        default="heuristic",

        help="Usage assumption inference mode (default: heuristic).",

    )

    parser.add_argument(

        "--scenario",

        action="append",

        dest="scenarios",

        metavar="ID",

        help="Run only the given scenario id (repeatable). Default: all scenarios.",

    )

    parser.add_argument(

        "--output-dir",

        type=Path,

        default=DEFAULT_REPORT_DIR,

        help=f"Directory for per-run report files (default: {DEFAULT_REPORT_DIR}).",

    )

    parser.add_argument(

        "--no-write",

        action="store_true",

        help="Skip writing report files to disk.",

    )

    args = parser.parse_args()



    selected = None

    if args.scenarios:

        unknown = [item for item in args.scenarios if item not in SCENARIOS_BY_ID]

        if unknown:

            valid = ", ".join(sorted(SCENARIOS_BY_ID))

            print(f"Unknown scenario id(s): {', '.join(unknown)}", file=sys.stderr)

            print(f"Valid ids: {valid}", file=sys.stderr)

            return 1

        selected = [SCENARIOS_BY_ID[item] for item in args.scenarios]



    calculator = build_gcp_cost_calculator()

    pipeline = GcpProjectCostingPipeline(GcpUsageInferenceEngine(), calculator)

    suite = GcpPricingValidationSuite(pipeline)

    report = suite.run(scenarios=selected, inference_mode=args.inference)



    formatter = GcpPricingValidationSuiteFormatter()



    if not args.no_write:

        args.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")

        summary_path = args.output_dir / f"gcp_suite_summary_{timestamp}.txt"

        summary_path.write_text(formatter.format_summary(report), encoding="utf-8")



        json_path = args.output_dir / f"gcp_suite_{timestamp}.json"

        json_path.write_text(formatter.format_json(report), encoding="utf-8")



        print(f"Wrote reports to {args.output_dir}")



    if args.json:

        print(formatter.format_json(report))

    else:

        print(formatter.format_summary(report))



    failed = sum(

        1

        for run in report.scenario_runs

        for check in run.validation_checks

        if check.status.value == "fail"

    )

    return 1 if failed else 0





if __name__ == "__main__":

    raise SystemExit(main())

