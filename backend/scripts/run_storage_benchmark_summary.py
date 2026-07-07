"""Run and summarize AWS benchmark at 1000 users."""
import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def main() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(BACKEND / "scripts" / "benchmark_aws_scenarios.py"),
            "--mode",
            "llm",
            "--users",
            "1000",
            "--json",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stderr.strip():
        print(result.stderr, file=sys.stderr)
    data = json.loads(result.stdout)
    out = BACKEND / "benchmark_1000.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print("=== MONTHLY COST @ 1,000 USERS ===")
    print(f"{'Scenario':<32} {'Source':<22} {'Total':>10} {'RDS':>10} {'S3':>10}")
    print("-" * 88)
    for s in data["scenarios"]:
        run = s["rows"][0]
        rds = next((c for c in run["components"] if c["aws_service"] == "RDS"), None)
        s3 = next((c for c in run["components"] if c["aws_service"] == "S3"), None)
        print(
            f"{s['name'][:32]:<32} {run['inference_source']:<22} "
            f"${run['total_usd']:>9.2f} "
            f"${(rds or {}).get('subtotal_usd', 0):>9.2f} "
            f"${(s3 or {}).get('subtotal_usd', 0):>9.2f}"
        )

    for s in data["scenarios"]:
        run = s["rows"][0]
        print(f"\n{'='*72}\n{s['name']} — ${run['total_usd']:.2f}/mo ({run['inference_source']})\n{'='*72}")
        for comp in run["components"]:
            if comp["aws_service"] not in {"RDS", "S3"}:
                continue
            print(f"\n  {comp['component_id']} ({comp['aws_service']}): ${comp['subtotal_usd']:.2f}")
            for a in comp["behavioral_assumptions"]:
                if a["key"].startswith("storage_") or a["key"] in {
                    "backup_retention_days",
                    "static_storage_gb",
                }:
                    print(f"    {a['key']}: {a['value']} {a['unit']}")
            for a in comp["resolved_assumptions"]:
                if a["key"] in {"storage_gb", "backup_storage_gb"}:
                    print(f"    resolved {a['key']}: {a['value']} {a['unit']}")


if __name__ == "__main__":
    main()
