"""Summarize pricing audit for quick review."""

from __future__ import annotations

import json
from pathlib import Path

data = json.loads(Path(__file__).parent.parent.joinpath("pricing_audit.json").read_text())

for sc in data["scenarios"]:
    totals = {p: 0.0 for p in ("aws", "gcp", "azure")}
    issues = []
    for comp in sc["components"]:
        name = comp["component"]["name"]
        for p in ("aws", "gcp", "azure"):
            audit = comp["providers"][p]
            totals[p] += audit["monthly_cost_min"]
        for flag in comp["cross_provider"].get("potential_issues", []):
            issues.append(f"{name}: {flag}")
    print(f"=== {sc['name']} ({sc['expected_users']} users, {sc['stage']}) ===")
    for p, t in totals.items():
        print(f"  {p.upper()}: ${t:,.2f}/mo")
    if issues:
        print("  Issues:")
        for i in issues[:12]:
            print(f"    - {i}")
        if len(issues) > 12:
            print(f"    ... and {len(issues)-12} more")
    print()
