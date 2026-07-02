"""Print scenario totals from validation_pricing_results.json."""

from __future__ import annotations

import json
from pathlib import Path

data = json.loads(Path(__file__).parent.parent.joinpath("validation_pricing_results.json").read_text())

for run in data:
    sc = run["scenario"]
    print(f"{sc['name']} ({sc['requirements']['expected_users']} users, {sc['requirements']['stage']})")
    for est in run["estimates"]:
        zeros = [
            c["component_name"]
            for c in est["components"]
            if c["monthly_cost_max"] == 0 and c["cloud_service"] not in ("N/A", "Stripe")
        ]
        print(
            f"  {est['provider']:5} ${est['monthly_low']:8.2f} - ${est['monthly_high']:8.2f}"
            + (f"  | $0: {', '.join(zeros)}" if zeros else "")
        )
    print()
