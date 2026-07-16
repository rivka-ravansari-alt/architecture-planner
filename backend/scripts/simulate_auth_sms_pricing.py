"""Simulate authentication SMS pricing for Cognito / Entra / Firebase Auth.

Uses seed pricing definitions in-memory (no Firestore) and the real static
resolver + usage-input builder + pricing executor path.

Run from the backend directory:

    python scripts/simulate_auth_sms_pricing.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.schemas.global_usage_model import GlobalUsageModelPayload, UsageParameterEstimate
from app.services.pricing_calculation_executor import execute_pricing_script
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_inputs_builder import build_usage_inputs
from scripts.seed_pricing_services import PRICING_SERVICES

EXPECTED_USERS = 10_000
STAGE = "mvp"

AUTH_SERVICE_IDS = (
    "aws_cognito",
    "azure_entra_id",
    "gcp_firebase_auth",
)


@dataclass(frozen=True)
class Case:
    name: str
    authentication_methods: list[str]
    llm_sms_verifications: float | None
    expect_sms_billed: bool


CASES: list[Case] = [
    Case(
        name="email_only_no_sms",
        authentication_methods=["email", "google"],
        llm_sms_verifications=0,
        expect_sms_billed=False,
    ),
    Case(
        name="sms_selected_llm_returns_zero_uses_default",
        authentication_methods=["email", "sms"],
        llm_sms_verifications=0,
        expect_sms_billed=True,
    ),
    Case(
        name="sms_selected_llm_returns_one",
        authentication_methods=["sms"],
        llm_sms_verifications=1,
        expect_sms_billed=True,
    ),
]


def _pricing_by_id() -> dict[str, dict[str, Any]]:
    return {
        item["service_id"]: item
        for item in PRICING_SERVICES
        if item.get("service_id") in AUTH_SERVICE_IDS
    }


def _requirements(methods: list[str]) -> dict[str, Any]:
    return {
        "authentication": {
            "enabled": True,
            "authentication_methods": methods,
        }
    }


def _expected_sms_price(
    *,
    service: dict[str, Any],
    users: int,
    sms_per_user: float,
) -> float:
    sms_sku = next(sku for sku in service["skus"] if sku["name"] == "SMS Verification")
    monthly_sms = users * sms_per_user
    free_sms = float(service.get("free_tier", {}).get("sms_per_month_estimate", 0) or 0)
    # Cognito has no SMS free tier; Entra/Firebase subtract sms_per_month_estimate.
    if "sms_per_month_estimate" in (service.get("free_tier") or {}):
        billable_sms = max(0.0, monthly_sms - free_sms)
    else:
        billable_sms = monthly_sms
    return round(billable_sms * float(sms_sku["price_per_sms"]), 2)


def _run_case(
    *,
    service: dict[str, Any],
    case: Case,
) -> tuple[bool, str]:
    service_id = service["service_id"]
    static_params = list(service.get("to_know", {}).get("static") or [])
    # Always resolve the auth static keys we care about for the sim.
    for key in ("users", "authentication_methods"):
        if key not in static_params:
            static_params.append(key)

    static_values = StaticUsageValueResolver().resolve(
        static_params,
        expected_users=EXPECTED_USERS,
        stage=STAGE,
        requirements=_requirements(case.authentication_methods),
    )

    llm: dict[str, UsageParameterEstimate] = {}
    if case.llm_sms_verifications is not None:
        llm["sms_verifications_per_user_per_month"] = UsageParameterEstimate(
            value=case.llm_sms_verifications,
            reason="Simulation fixture.",
        )

    inputs = build_usage_inputs(
        GlobalUsageModelPayload(llm=llm, static=static_values)
    )
    result = execute_pricing_script(
        service["script_calculation"],
        inputs=inputs,
        skus=service.get("skus") or [],
        free_tier=service.get("free_tier") or {},
        to_know=service.get("to_know"),
        service_id=service_id,
    )

    methods = inputs.get("authentication_methods")
    sms_per_user = float(inputs.get("sms_verifications_per_user_per_month") or 0)
    summary = "; ".join(result.calculation_summary)

    # With 10K users, Cognito/Entra/Firebase MAU free tiers cover MAU cost.
    expected_mau = 0.0
    expected_sms = 0.0
    if case.expect_sms_billed:
        expected_sms = _expected_sms_price(
            service=service,
            users=EXPECTED_USERS,
            sms_per_user=sms_per_user,
        )
    expected_total = round(expected_mau + expected_sms, 2)

    ok = result.monthly_price == expected_total
    if case.expect_sms_billed:
        ok = ok and expected_sms > 0 and "sms" in (methods or [])

    status = "PASS" if ok else "FAIL"
    detail = (
        f"[{status}] {service_id} / {case.name}\n"
        f"  methods={methods} sms_per_user={sms_per_user}\n"
        f"  price={result.monthly_price} expected={expected_total} "
        f"(mau={expected_mau}, sms={expected_sms})\n"
        f"  summary: {summary}"
    )
    return ok, detail


def main() -> int:
    services = _pricing_by_id()
    missing = [sid for sid in AUTH_SERVICE_IDS if sid not in services]
    if missing:
        print(f"Missing seed pricing services: {', '.join(missing)}")
        return 2

    print("=" * 78)
    print("Auth SMS pricing simulation")
    print(f"users={EXPECTED_USERS} stage={STAGE}")
    print("=" * 78)

    failures = 0
    for service_id in AUTH_SERVICE_IDS:
        service = services[service_id]
        print(f"\n### {service_id}")
        print(f"to_know={service.get('to_know')}")
        print(f"free_tier={service.get('free_tier')}")
        for case in CASES:
            ok, detail = _run_case(service=service, case=case)
            print(detail)
            if not ok:
                failures += 1

    print("\n" + "=" * 78)
    if failures:
        print(f"RESULT: {failures} failure(s)")
        return 1
    print("RESULT: all cases passed — SMS pricing works in the seed pipeline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
