"""Inspect high-cost components in validation results."""

from __future__ import annotations

import json
from pathlib import Path

data = json.loads(Path(__file__).parent.parent.joinpath("validation_pricing_results.json").read_text())

for run in data:
    name = run["scenario"]["name"]
    if name not in ("ShopLite", "HealthPortal", "SocialFeed", "TaskFlow"):
        continue
    print(f"=== {name} ===")
    for est in run["estimates"]:
        prov = est["provider"]
        print(f"{prov} TOTAL ${est['monthly_low']:.2f} - ${est['monthly_high']:.2f}")
        for c in sorted(est["components"], key=lambda x: -x["monthly_cost_max"]):
            if c["monthly_cost_max"] >= 0.5 or c["monthly_cost_max"] == 0:
                skus = "; ".join(f"{s['role']}:${s['cost_usd']:.2f}" for s in c["matched_skus"])
                print(
                    f"  {c['component_name']}: ${c['monthly_cost_min']:.2f}-${c['monthly_cost_max']:.2f} "
                    f"[{c['confidence']}] {c['cloud_service']}"
                )
                print(f"    SKUs: {skus or 'none'}")
        print()
