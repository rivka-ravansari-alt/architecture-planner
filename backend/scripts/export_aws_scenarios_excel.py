"""Run 20 AWS pricing scenarios and export a single-sheet Excel workbook."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pricing.aws.scenarios import AWS_TWENTY_SCENARIOS
from app.pricing.aws.scenario_excel_export import (
    build_exporter,
    write_scenario_excel,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "pricing-validation" / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 20 AWS scenarios (LLM usage inference + catalog pricing) and export Excel.",
    )
    parser.add_argument(
        "--mode",
        choices=("llm", "heuristic"),
        default="llm",
        help="Usage inference mode (default: llm).",
    )
    parser.add_argument(
        "--catalog",
        choices=("firestore",),
        default="firestore",
        help="Pricing catalog source (Firestore only).",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1_000,
        help="Monthly active users for every scenario (default: 1000).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .xlsx path (default: docs/pricing-validation/reports/aws_scenarios_<timestamp>.xlsx).",
    )
    args = parser.parse_args()

    if len(AWS_TWENTY_SCENARIOS) != 20:
        print(
            f"Expected 20 scenarios, found {len(AWS_TWENTY_SCENARIOS)}.",
            file=sys.stderr,
        )
        return 1

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output or (DEFAULT_OUTPUT_DIR / f"aws_scenarios_{timestamp}.xlsx")

    exporter = build_exporter(
        inference_mode=args.mode,
        catalog=args.catalog,
        users=args.users,
    )
    results = exporter.run_all()
    written = write_scenario_excel(
        results,
        output_path,
        inference_mode=args.mode,
        catalog=args.catalog,
    )

    print(f"\nWrote {written}")
    print(f"Scenarios: {len(results)} | Users: {args.users:,} | Mode: {args.mode}")
    for item in results:
        print(f"  - {item.product_name}: ${item.total_usd:,.2f} ({item.inference_source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
