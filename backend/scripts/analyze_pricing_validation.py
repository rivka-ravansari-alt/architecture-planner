"""Analyze validation_pricing_results.json for pricing issues."""

from __future__ import annotations

import json
from pathlib import Path

data = json.loads(Path(__file__).parent.parent.joinpath("validation_pricing_results.json").read_text())

BILLABLE_TYPES = {
    "web_app",
    "api_gateway",
    "app_service",
    "database",
    "object_storage",
    "auth",
    "cdn",
    "cache",
    "queue",
    "queue_worker",
    "ai_provider",
    "monitoring",
    "load_balancer",
}


def main() -> None:
    issues: list[tuple] = []
    for run in data:
        sname = run["scenario"]["name"]
        users = run["scenario"]["requirements"]["expected_users"]
        stage = run["scenario"]["requirements"]["stage"]
        for est in run["estimates"]:
            prov = est["provider"]
            for comp in est["components"]:
                lo, hi = comp["monthly_cost_min"], comp["monthly_cost_max"]
                ctype = comp["component_type"]
                svc = comp["cloud_service"]
                conf = comp["confidence"]
                missing = comp["missing_data"]
                skus = comp["matched_skus"]

                if (
                    lo == 0
                    and hi == 0
                    and ctype in BILLABLE_TYPES
                    and svc not in ("N/A", "Stripe")
                ):
                    issues.append(("ZERO", sname, prov, comp["component_name"], ctype, svc, missing, conf))

                if hi > 500 and users in ("100", "1000") and stage == "mvp":
                    issues.append(("HIGH", sname, prov, comp["component_name"], hi, [s["role"] for s in skus]))
                if hi > 5000 and users == "10000":
                    issues.append(("HIGH", sname, prov, comp["component_name"], hi, [s["role"] for s in skus]))

                if hi < 0.01 and ctype in ("database", "app_service", "object_storage") and users == "10000":
                    issues.append(("LOW", sname, prov, comp["component_name"], hi, conf))

                if not skus and hi > 0:
                    issues.append(("NO_SKU_COST", sname, prov, comp["component_name"], hi))

                if ctype == "auth" and "API Gateway" in svc:
                    issues.append(("WRONG_SVC", sname, prov, comp["component_name"], svc))

                if ctype == "cdn" and svc == "Networking":
                    issues.append(("VAGUE_SVC", sname, prov, comp["component_name"], svc))

            if est["monthly_high"] > 2000 and users in ("100", "1000"):
                issues.append(("TOTAL_HIGH", sname, prov, est["monthly_high"]))

    print("ISSUE SUMMARY")
    print("=" * 60)
    for item in issues:
        print(item)
    print(f"\nTotal issues flagged: {len(issues)}\n")

    for run in data:
        print("=" * 60)
        sc = run["scenario"]
        print(f"SCENARIO: {sc['name']} - {sc['description']}")
        print(f"Users: {sc['requirements']['expected_users']} | Stage: {sc['requirements']['stage']}")
        print(f"Requirements: { {k:v for k,v in sc['requirements'].items() if k not in ('expected_users','stage') and v} }")
        print()
        for est in run["estimates"]:
            print(f"  [{est['provider'].upper()}] TOTAL: ${est['monthly_low']:.2f} - ${est['monthly_high']:.2f}/mo")
            for comp in est["components"]:
                skus = ", ".join(f"{s['role']}(${s['cost_usd']:.4f})" for s in comp["matched_skus"]) or "—"
                print(
                    f"    - {comp['component_name']} ({comp['component_type']}) -> {comp['cloud_service']}"
                    f" | ${comp['monthly_cost_min']:.2f}-${comp['monthly_cost_max']:.2f}"
                    f" | {comp['confidence']} | SKUs: {skus}"
                )
                if comp["missing_data"]:
                    print(f"      missing: {comp['missing_data']}")
            print()


if __name__ == "__main__":
    main()
