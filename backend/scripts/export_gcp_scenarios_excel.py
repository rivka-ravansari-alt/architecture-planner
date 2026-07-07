"""Run five GCP pricing scenarios across user counts and export Excel benchmark report."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pricing.gcp.scenario_excel_export import (
    GCP_FIVE_SCENARIOS,
    build_exporter,
    write_gcp_scenario_excel,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "pricing-validation" / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run 5 GCP benchmark scenarios (Simple CRUD, Self-Esteem, E-Commerce, "
            "AI Chat, AI Document OCR) at 100/1K/10K/100K users and export Excel."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("llm", "heuristic"),
        default="heuristic",
        help="Usage inference mode (default: heuristic for reproducible offline runs).",
    )
    parser.add_argument(
        "--catalog",
        choices=("firestore",),
        default="firestore",
        help="Pricing catalog source (Firestore only).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .xlsx path (default: docs/pricing-validation/reports/gcp_scenarios_<timestamp>.xlsx).",
    )
    args = parser.parse_args()

    if len(GCP_FIVE_SCENARIOS) != 5:
        print(f"Expected 5 scenarios, found {len(GCP_FIVE_SCENARIOS)}.", file=sys.stderr)
        return 1

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output or (DEFAULT_OUTPUT_DIR / f"gcp_scenarios_{timestamp}.xlsx")

    exporter = build_exporter(inference_mode=args.mode, catalog=args.catalog)
    runs = exporter.run_all()
    written = write_gcp_scenario_excel(
        runs,
        output_path,
        inference_mode=args.mode,
        catalog=args.catalog,
    )

    print(f"\nWrote {written}")
    print(f"Scenarios: {len(GCP_FIVE_SCENARIOS)} | User counts: 100, 1K, 10K, 100K | Mode: {args.mode}")
    print("\nSummary (monthly USD):")
    print(f"{'Scenario':<32} {'100':>12} {'1K':>12} {'10K':>12} {'100K':>12}")
    print("-" * 80)
    by_scenario: dict[str, dict[int, float]] = {}
    for run in runs:
        by_scenario.setdefault(run.scenario.name, {})[run.users] = run.report.total_usd
    for scenario in GCP_FIVE_SCENARIOS:
        totals = by_scenario.get(scenario.name, {})
        print(
            f"{scenario.name[:32]:<32}"
            f"{totals.get(100, 0.0):>12,.2f}"
            f"{totals.get(1_000, 0.0):>12,.2f}"
            f"{totals.get(10_000, 0.0):>12,.2f}"
            f"{totals.get(100_000, 0.0):>12,.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
