"""Debug why Cognito SMS pricing is $0 against live Firestore data.

Checks:
1. aws_cognito pricing_services document has SMS script / to_know
2. Latest project requirements include authentication_methods with sms
3. Latest usage model static/llm values
4. Recomputes Cognito price with current seed-equivalent path

Run from backend:

    python scripts/debug_auth_sms_live.py
    python scripts/debug_auth_sms_live.py --project-id <id>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.firestore_client import get_firestore_client
from app.config.params import (
    FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION,
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
)
from app.repositories.pricing_service_repository import PricingServiceRepository
from app.schemas.global_usage_model import (
    GlobalUsageModelPayload,
    UsageParameterEstimate,
    coerce_static_usage_value,
)
from app.services.pricing_calculation_executor import execute_pricing_script
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_inputs_builder import build_usage_inputs


def _print(label: str, payload: Any) -> None:
    print(f"\n{label}:")
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, default=str, sort_keys=True))


def _latest_doc(collection_ref):
    docs = list(
        collection_ref.order_by("created_at", direction="DESCENDING").limit(1).stream()
    )
    if not docs:
        return None
    data = docs[0].to_dict() or {}
    data["id"] = docs[0].id
    return data


def _find_latest_project_id(client) -> str | None:
    best: tuple[Any, str] | None = None
    for snapshot in client.collection(FIRESTORE_PROJECTS_COLLECTION).stream():
        usage = _latest_doc(
            snapshot.reference.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
        )
        created = None if usage is None else usage.get("created_at")
        if best is None or (created is not None and (best[0] is None or created > best[0])):
            best = (created, snapshot.id)
    return None if best is None else best[1]


def _usage_payload(document: dict[str, Any]) -> GlobalUsageModelPayload:
    usage_model = document.get("usage_model") or {}
    llm_payload = usage_model.get("llm") or {}
    static_payload = usage_model.get("static") or {}
    llm = {
        key: UsageParameterEstimate.model_validate(value)
        for key, value in llm_payload.items()
    }
    static: dict[str, Any] = {}
    for key, value in static_payload.items():
        coerced = coerce_static_usage_value(value)
        if coerced is not None:
            static[key] = coerced
    return GlobalUsageModelPayload(llm=llm, static=static)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", default="")
    args = parser.parse_args()

    client = get_firestore_client()
    pricing_repo = PricingServiceRepository(client)
    cognito = pricing_repo.find_by_id("aws_cognito")
    if cognito is None:
        print("FAIL: aws_cognito missing from Firestore pricing_services")
        return 2

    script = cognito.get("script_calculation") or ""
    to_know = cognito.get("to_know") or {}
    has_sms_check = '"sms" in authentication_methods' in script
    has_auth_static = "authentication_methods" in (to_know.get("static") or [])
    has_sms_llm = "sms_verifications_per_user_per_month" in (to_know.get("llm") or [])

    print("=" * 78)
    print("1) Firestore aws_cognito definition")
    print("=" * 78)
    _print("to_know", to_know)
    _print("free_tier", cognito.get("free_tier"))
    _print(
        "script checks",
        {
            "has_sms_in_methods_check": has_sms_check,
            "has_authentication_methods_static": has_auth_static,
            "has_sms_verifications_llm": has_sms_llm,
            "script_contains_SMS_Verification": "SMS Verification" in script,
        },
    )
    if not (has_sms_check and has_auth_static and has_sms_llm):
        print(
            "\nDIAGNOSIS: Firestore Cognito definition is STALE. "
            "Run: python scripts/seed_pricing_services.py"
        )

    project_id = args.project_id.strip() or _find_latest_project_id(client)
    if not project_id:
        print("\nNo project found to debug.")
        return 1

    project_ref = client.collection(FIRESTORE_PROJECTS_COLLECTION).document(project_id)
    project_snap = project_ref.get()
    if not project_snap.exists:
        print(f"\nProject not found: {project_id}")
        return 1
    project = project_snap.to_dict() or {}
    project["id"] = project_id

    print("\n" + "=" * 78)
    print(f"2) Project {project_id}")
    print("=" * 78)
    requirements = project.get("requirements") or {}
    auth = requirements.get("authentication") or {}
    _print(
        "project auth slice",
        {
            "expected_users": project.get("expected_users"),
            "stage": project.get("stage"),
            "authentication": auth,
        },
    )
    methods = auth.get("authentication_methods") if isinstance(auth, dict) else None
    if not isinstance(methods, list) or "sms" not in methods:
        print(
            "\nDIAGNOSIS: Project requirements do NOT include authentication_methods "
            "with 'sms'. Step 1 must save SMS selected, then regenerate usage + pricing."
        )

    usage = _latest_doc(
        project_ref.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
    )
    selection = _latest_doc(
        project_ref.collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
    )

    print("\n" + "=" * 78)
    print("3) Latest usage model")
    print("=" * 78)
    if usage is None:
        print("No usage model saved.")
        return 1

    usage_model = usage.get("usage_model") or {}
    _print(
        "usage model keys",
        {
            "usage_id": usage.get("id"),
            "selection_id": usage.get("selection_id"),
            "static_parameters": usage.get("static_parameters"),
            "llm_parameters": usage.get("llm_parameters"),
            "static": usage_model.get("static"),
            "llm": {
                key: (
                    estimate
                    if not isinstance(estimate, dict)
                    else {"value": estimate.get("value"), "reason": estimate.get("reason")}
                )
                for key, estimate in (usage_model.get("llm") or {}).items()
            },
        },
    )
    static = usage_model.get("static") or {}
    if "authentication_methods" not in static:
        print(
            "\nDIAGNOSIS: Saved usage model static is missing authentication_methods. "
            "Regenerate Step 3 AFTER reseeding pricing services."
        )
    elif "sms" not in (static.get("authentication_methods") or []):
        print(
            "\nDIAGNOSIS: Saved authentication_methods has no 'sms'. "
            "Update Step 1 methods and regenerate usage."
        )

    print("\n" + "=" * 78)
    print("4) Recompute Cognito with SAVED usage model")
    print("=" * 78)
    payload = _usage_payload(usage)
    inputs = build_usage_inputs(payload)
    _print("pricing inputs (after defaults)", {
        "users": inputs.get("users"),
        "authentication_methods": inputs.get("authentication_methods"),
        "sms_verifications_per_user_per_month": inputs.get(
            "sms_verifications_per_user_per_month"
        ),
    })
    result = execute_pricing_script(
        script,
        inputs=inputs,
        skus=cognito.get("skus") or [],
        free_tier=cognito.get("free_tier") or {},
        to_know=to_know,
        service_id="aws_cognito",
    )
    _print(
        "recomputed price",
        {
            "monthly_price": result.monthly_price,
            "calculation_summary": result.calculation_summary,
        },
    )

    print("\n" + "=" * 78)
    print("5) Recompute from project requirements (fresh static resolve)")
    print("=" * 78)
    fresh_static = StaticUsageValueResolver().resolve(
        ["users", "authentication_methods"],
        expected_users=int(project.get("expected_users") or 0),
        stage=str(project.get("stage") or "mvp"),
        requirements=requirements if isinstance(requirements, dict) else {},
    )
    llm = {}
    saved_llm = (usage_model.get("llm") or {}).get("sms_verifications_per_user_per_month")
    if isinstance(saved_llm, dict):
        llm["sms_verifications_per_user_per_month"] = UsageParameterEstimate.model_validate(
            saved_llm
        )
    else:
        llm["sms_verifications_per_user_per_month"] = UsageParameterEstimate(
            value=0, reason="Debug default before usage-input fallback."
        )
    fresh_inputs = build_usage_inputs(
        GlobalUsageModelPayload(llm=llm, static=fresh_static)
    )
    fresh_result = execute_pricing_script(
        script,
        inputs=fresh_inputs,
        skus=cognito.get("skus") or [],
        free_tier=cognito.get("free_tier") or {},
        to_know=to_know,
        service_id="aws_cognito",
    )
    _print("fresh static from requirements", fresh_static)
    _print(
        "fresh recompute",
        {
            "inputs": {
                "users": fresh_inputs.get("users"),
                "authentication_methods": fresh_inputs.get("authentication_methods"),
                "sms_verifications_per_user_per_month": fresh_inputs.get(
                    "sms_verifications_per_user_per_month"
                ),
            },
            "monthly_price": fresh_result.monthly_price,
            "calculation_summary": fresh_result.calculation_summary,
        },
    )

    if selection is not None:
        print(f"\nLatest selection id: {selection.get('id')}")

    if result.monthly_price == 0 and fresh_result.monthly_price > 0:
        print(
            "\nROOT CAUSE: Saved usage model is stale / missing SMS methods. "
            "Reseed is OK, but you must regenerate the usage model, then pricing."
        )
    elif result.monthly_price == 0 and fresh_result.monthly_price == 0:
        print(
            "\nROOT CAUSE: Requirements do not include sms (or Cognito script still stale)."
        )
    elif result.monthly_price > 0:
        print(
            "\nCognito SMS pricing WORKS with current Firestore data. "
            "If the UI still shows $0, regenerate a new pricing run (stale run cached)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
