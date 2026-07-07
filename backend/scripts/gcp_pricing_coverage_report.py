"""Generate GCP pricing coverage report."""



from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path



sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



from app.pricing.gcp.coverage import build_gcp_pricing_coverage_report





def _bool_label(value: bool) -> str:

    return "yes" if value else "no"





def format_text_report(report) -> str:

    lines = [

        "GCP PRICING COVERAGE REPORT",

        "=" * 100,

        "",

        f"{'Service':<32} {'Types':<18} {'Model':>5} {'SKU':>5} {'Roles':>5} "

        f"{'Behav':>5} {'Free':>5} {'Cat':>5} {'Group':>5} {'Supported':>9}",

        "-" * 100,

    ]

    for item in report.services:

        types = ",".join(item.component_types[:2])

        if len(item.component_types) > 2:

            types += "…"

        lines.append(

            f"{item.service_name[:32]:<32} {types[:18]:<18} "

            f"{_bool_label(item.pricing_model):>5} "

            f"{_bool_label(item.sku_calculator):>5} "

            f"{_bool_label(item.sku_role_mapping):>5} "

            f"{_bool_label(item.behavioral_model):>5} "

            f"{_bool_label(item.free_tier):>5} "

            f"{_bool_label(item.test_catalog_fixture):>5} "

            f"{item.coverage_group:>5} "

            f"{_bool_label(item.fully_supported):>9}"

        )



    lines.extend(["", "GAP GROUPS", ""])

    for group_key, names in report.by_group.items():

        lines.append(f"{group_key}: {len(names)}")

        for name in names:

            item = next(s for s in report.services if s.service_name == name)

            extra = f" — {item.deferred_reason}" if item.deferred_reason else ""

            gaps = f" ({', '.join(item.gaps)})" if item.gaps else ""

            lines.append(f"  - {name}{extra}{gaps}")

        lines.append("")



    lines.append("FALLBACK BEHAVIOR SUMMARY")

    for item in report.services:

        if not item.fully_supported:

            lines.append(f"  {item.service_name}: {item.fallback_behavior}")



    return "\n".join(lines)





def main() -> None:

    parser = argparse.ArgumentParser(description="GCP pricing coverage report.")

    parser.add_argument("--json", action="store_true", help="Output JSON.")

    args = parser.parse_args()



    report = build_gcp_pricing_coverage_report()

    if args.json:

        payload = {

            "services": [

                {

                    "service_name": item.service_name,

                    "canonical_service": item.canonical_service,

                    "component_types": list(item.component_types),

                    "is_default_mapping": item.is_default_mapping,

                    "pricing_model": item.pricing_model,

                    "sku_calculator": item.sku_calculator,

                    "sku_role_mapping": item.sku_role_mapping,

                    "behavioral_model": item.behavioral_model,

                    "free_tier": item.free_tier,

                    "test_catalog_fixture": item.test_catalog_fixture,

                    "fully_supported": item.fully_supported,

                    "coverage_group": item.coverage_group,

                    "gaps": list(item.gaps),

                    "deferred_reason": item.deferred_reason,

                    "fallback_behavior": item.fallback_behavior,

                }

                for item in report.services

            ],

            "by_group": report.by_group,

            "fully_supported": report.fully_supported,

            "unsupported": report.unsupported,

            "ui_only": report.ui_only,

        }

        print(json.dumps(payload, indent=2))

        return



    print(format_text_report(report))





if __name__ == "__main__":

    main()

