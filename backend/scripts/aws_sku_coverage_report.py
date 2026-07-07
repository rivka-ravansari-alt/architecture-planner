"""Run AWS SKU pricing coverage audit against benchmark scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pricing.aws.sku_pricing_audit import build_auditor, format_audit_report

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "pricing-validation" / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(description="AWS SKU pricing coverage audit.")
    parser.add_argument("--mode", choices=("llm", "heuristic"), default="heuristic")
    parser.add_argument("--catalog", choices=("firestore",), default="firestore")
    parser.add_argument("--users", type=int, default=1_000)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    auditor = build_auditor(
        inference_mode=args.mode,
        users=args.users,
        catalog=args.catalog,
    )
    report = auditor.run()

    if args.json:
        payload = {
            "users": report.users,
            "inference_mode": report.inference_mode,
            "scenario_count": report.scenario_count,
            "by_service": {
                key: summary.__dict__ for key, summary in report.by_service.items()
            },
            "underpriced_scenarios": report.underpriced_scenarios,
            "partial_components": report.partial_components,
            "lines": [line.__dict__ for line in report.lines],
        }
        print(json.dumps(payload, indent=2))
        return 0

    text = format_audit_report(report)
    print(text)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    path = args.output_dir / f"aws_sku_coverage_{timestamp}.txt"
    path.write_text(text, encoding="utf-8")
    print(f"\nWrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
