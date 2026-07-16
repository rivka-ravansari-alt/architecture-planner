"""Debug Cloud SQL package selection for a project."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from app.clients.firestore_client import get_firestore_client
from app.config.params import (
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PRICING_RUNS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
    FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION,
)
from app.repositories.pricing_service_repository import PricingServiceRepository
from app.schemas.global_usage_model import (
    GlobalUsageModelPayload,
    UsageParameterEstimate,
    coerce_static_usage_value,
)
from app.services.pricing_calculation_executor import execute_pricing_script
from app.services.pricing_service import PricingService
from app.services.usage_inputs_builder import build_usage_inputs


CLOUD_SQL_PARAMS = ("cpu", "ram_gb", "database_storage_gb")


def _usage_payload_from_document(document: dict[str, Any]) -> GlobalUsageModelPayload:
    usage_model = document.get("usage_model") or {}
    llm_payload = usage_model.get("llm") or document.get("usage") or {}
    static_payload = usage_model.get("static") or document.get("static") or {}

    llm = {
        parameter: UsageParameterEstimate.model_validate(estimate)
        for parameter, estimate in llm_payload.items()
    }
    static: dict[str, str | int | float | list[str]] = {}
    for parameter, value in static_payload.items():
        coerced = coerce_static_usage_value(value)
        if coerced is not None:
            static[parameter] = coerced

    return GlobalUsageModelPayload(llm=llm, static=static)


def _match_package(
    *,
    required_cpu: float,
    required_ram_gb: float,
    required_database_storage_gb: float,
    sku: dict[str, Any],
) -> dict[str, bool]:
    cpu_match = sku["cpu"] >= required_cpu
    ram_match = sku["ram_gb"] >= required_ram_gb
    storage_match = sku["database_storage_gb"] >= required_database_storage_gb
    return {
        "cpu_match": cpu_match,
        "ram_match": ram_match,
        "storage_match": storage_match,
        "overall_match": cpu_match and ram_match and storage_match,
    }


def _select_package(
    *,
    required_cpu: float,
    required_ram_gb: float,
    required_database_storage_gb: float,
    skus: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    matching: list[dict[str, Any]] = []
    for sku in skus:
        flags = _match_package(
            required_cpu=required_cpu,
            required_ram_gb=required_ram_gb,
            required_database_storage_gb=required_database_storage_gb,
            sku=sku,
        )
        if flags["overall_match"]:
            matching.append(sku)

    if not matching:
        return None, []

    selected = min(
        matching,
        key=lambda sku: (
            sku["monthly_price"],
            sku["cpu"],
            sku["ram_gb"],
            sku["database_storage_gb"],
        ),
    )
    return selected, matching


def _find_latest_project_with_cloud_sql(client) -> str | None:
    projects = client.collection(FIRESTORE_PROJECTS_COLLECTION).stream()
    best: tuple[Any, str] | None = None

    for project in projects:
        models = list(
            project.reference.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .order_by("created_at", direction="DESCENDING")
            .limit(1)
            .stream()
        )
        if not models:
            continue
        model = models[0].to_dict() or {}
        llm = (model.get("usage_model") or {}).get("llm") or model.get("usage") or {}
        if not any(param in llm for param in CLOUD_SQL_PARAMS):
            continue
        created_at = model.get("created_at")
        if best is None or (created_at and created_at > best[0]):
            best = (created_at, project.id)

    return best[1] if best else None


def _get_gcp_cloud_sql_line_item(client, project_id: str) -> dict[str, Any] | None:
    runs = list(
        client.collection(FIRESTORE_PROJECTS_COLLECTION)
        .document(project_id)
        .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    if not runs:
        return None

    gcp = (
        runs[0]
        .reference.collection(FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION)
        .document("gcp")
        .get()
    )
    if not gcp.exists:
        return None

    data = gcp.to_dict() or {}
    for item in data.get("line_items") or []:
        if item.get("service_id") == "gcp_cloud_sql":
            return item
    return None


def debug_project(project_id: str) -> int:
    client = get_firestore_client()
    pricing_repo = PricingServiceRepository(client)

    project_ref = client.collection(FIRESTORE_PROJECTS_COLLECTION).document(project_id)
    if not project_ref.get().exists:
        print(f"Project not found: {project_id}")
        return 1

    usage_docs = list(
        project_ref.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    if not usage_docs:
        print(f"No global usage model for project {project_id}")
        return 1

    usage_document = usage_docs[0].to_dict() or {}
    usage_document["id"] = usage_docs[0].id
    payload = _usage_payload_from_document(usage_document)
    usage_inputs = build_usage_inputs(payload)

    pricing_service = pricing_repo.find_by_id("gcp_cloud_sql")
    if pricing_service is None:
        print("gcp_cloud_sql pricing service not found in Firestore")
        return 1

    skus = pricing_service.get("skus") or []
    script = pricing_service.get("script_calculation", "")
    free_tier = pricing_service.get("free_tier") or {}

    required_cpu = max(0, float(usage_inputs.get("cpu", 0) or 0))
    required_ram_gb = max(0, float(usage_inputs.get("ram_gb", 0) or 0))
    required_database_storage_gb = max(0, float(usage_inputs.get("database_storage_gb", 0) or 0))

    print(f"Project: {project_id}")
    print(f"Usage model: {usage_document['id']}")
    print()
    print("LLM values used by pricing (flat usage_inputs):")
    for param in CLOUD_SQL_PARAMS:
        llm_estimate = payload.llm.get(param)
        if llm_estimate:
            print(
                f"  {param}: {llm_estimate.value} "
                f"(reason: {llm_estimate.reason})"
            )
        else:
            print(f"  {param}: <missing from LLM payload>")
    print()
    print("Values passed into calculate_price():")
    print(f"  cpu: {required_cpu}")
    print(f"  ram_gb: {required_ram_gb}")
    print(f"  database_storage_gb: {required_database_storage_gb}")
    print()

    print("Available Cloud SQL packages:")
    for sku in skus:
        print(
            f"  - {sku['name']}: cpu={sku['cpu']}, ram_gb={sku['ram_gb']}, "
            f"database_storage_gb={sku['database_storage_gb']}, monthly_price=${sku['monthly_price']}"
        )
    print()

    print("Package matching:")
    for sku in skus:
        flags = _match_package(
            required_cpu=required_cpu,
            required_ram_gb=required_ram_gb,
            required_database_storage_gb=required_database_storage_gb,
            sku=sku,
        )
        print(f"  {sku['name']}:")
        print(f"    cpu match: {flags['cpu_match']} ({sku['cpu']} >= {required_cpu})")
        print(
            f"    ram match: {flags['ram_match']} "
            f"({sku['ram_gb']} >= {required_ram_gb})"
        )
        print(
            f"    storage match: {flags['storage_match']} "
            f"({sku['database_storage_gb']} >= {required_database_storage_gb})"
        )
        print(f"    overall match: {flags['overall_match']}")
    print()

    selected, matching = _select_package(
        required_cpu=required_cpu,
        required_ram_gb=required_ram_gb,
        required_database_storage_gb=required_database_storage_gb,
        skus=skus,
    )
    calculated_price = execute_pricing_script(
        script,
        inputs=usage_inputs,
        skus=skus,
        free_tier=free_tier,
    ).monthly_price

    if selected is None:
        print("Selected package: none (no package matched)")
    else:
        print(f"Selected package: {selected['name']}")
        print(f"Calculated monthly price: ${calculated_price}")
        print()
        print("Why this package was chosen:")
        print(
            "  Rule: pick the cheapest matching package by "
            "(monthly_price, cpu, ram_gb, database_storage_gb)."
        )
        print(f"  Matching packages: {[sku['name'] for sku in matching]}")
        if len(matching) > 1:
            print("  Tie-break order among matches:")
            for sku in sorted(
                matching,
                key=lambda entry: (
                    entry["monthly_price"],
                    entry["cpu"],
                    entry["ram_gb"],
                    entry["database_storage_gb"],
                ),
            ):
                print(
                    f"    {sku['name']}: price=${sku['monthly_price']}, "
                    f"cpu={sku['cpu']}, ram_gb={sku['ram_gb']}, database_storage_gb={sku['database_storage_gb']}"
                )

        failing = []
        for sku in skus:
            flags = _match_package(
                required_cpu=required_cpu,
                required_ram_gb=required_ram_gb,
                required_database_storage_gb=required_database_storage_gb,
                sku=sku,
            )
            if not flags["overall_match"]:
                reasons = []
                if not flags["cpu_match"]:
                    reasons.append(f"cpu {sku['cpu']} < required {required_cpu}")
                if not flags["ram_match"]:
                    reasons.append(
                        f"ram_gb {sku['ram_gb']} < required {required_ram_gb}"
                    )
                if not flags["storage_match"]:
                    reasons.append(
                        f"database_storage_gb {sku['database_storage_gb']} "
                        f"< required {required_database_storage_gb}"
                    )
                failing.append(f"{sku['name']} excluded: {', '.join(reasons)}")
        for line in failing:
            print(f"  {line}")

    line_item = _get_gcp_cloud_sql_line_item(client, project_id)
    if line_item:
        print()
        print("Stored GCP pricing line item:")
        print(f"  service: {line_item.get('service_name')}")
        print(f"  monthly_price: ${line_item.get('monthly_price')}")
    else:
        print()
        print("No stored gcp_cloud_sql line item found for the latest pricing run.")

    other_cpu_users = [
        param
        for param, estimate in payload.llm.items()
        if param == "cpu"
    ]
    if required_cpu < 1:
        print()
        print(
            "Note: cpu < 1 often comes from Cloud Functions (fractional vCPU), "
            "which shares the parameter name 'cpu' with Cloud SQL (integer cores)."
        )

    all_llm_params = sorted(payload.llm.keys())
    if "cpu" in all_llm_params:
        print()
        print("All LLM parameters in this project's usage model:")
        for param in all_llm_params:
            estimate = payload.llm[param]
            print(f"  {param}: {estimate.value}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Firestore project id (defaults to latest project with Cloud SQL LLM values)",
    )
    args = parser.parse_args(argv)

    project_id = args.project_id
    if not project_id:
        client = get_firestore_client()
        project_id = _find_latest_project_with_cloud_sql(client)
        if not project_id:
            print("No project with Cloud SQL LLM values found.")
            return 1
        print(f"Using latest project with Cloud SQL values: {project_id}\n")

    return debug_project(project_id)


if __name__ == "__main__":
    raise SystemExit(main())
