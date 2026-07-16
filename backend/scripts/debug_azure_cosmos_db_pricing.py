"""Debug Azure Cosmos DB pricing for a project."""

from __future__ import annotations

import argparse
import math
import sys
from typing import Any

from app.clients.firestore_client import get_firestore_client
from app.config.params import (
    FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION,
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PRICING_RUNS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
    FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION,
)
from app.repositories.cloud_service_mapping_repository import CloudServiceMappingRepository
from app.repositories.pricing_service_repository import PricingServiceRepository
from app.schemas.global_usage_model import GlobalUsageModelPayload, UsageParameterEstimate
from app.services.pricing_calculation_executor import execute_pricing_script
from app.services.usage_inputs_builder import build_usage_inputs

COSMOS_LLM_PARAMS = (
    "capacity_mode",
    "request_units_per_month",
    "request_units_per_user_per_month",
    "required_ru_per_second",
    "database_storage_gb",
)

SERVERLESS_PRICE_FIELDS = ("price_per_million_ru", "storage_price_per_gb_month")
PROVISIONED_PRICE_FIELDS = (
    "throughput_unit_ru_per_second",
    "price_per_100_ru_hour",
    "storage_price_per_gb_month",
)


def _usage_payload_from_document(document: dict[str, Any]) -> GlobalUsageModelPayload:
    usage_model = document.get("usage_model") or {}
    llm_payload = usage_model.get("llm") or document.get("usage") or {}
    static_payload = usage_model.get("static") or document.get("static") or {}

    llm = {
        parameter: UsageParameterEstimate.model_validate(estimate)
        for parameter, estimate in llm_payload.items()
    }
    static: dict[str, str | int | float] = {}
    for parameter, value in static_payload.items():
        if isinstance(value, (str, int, float)):
            static[parameter] = value

    return GlobalUsageModelPayload(llm=llm, static=static)


def _find_latest_project_with_cosmos_params(client) -> str | None:
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
        if not any(param in llm for param in COSMOS_LLM_PARAMS):
            continue
        created_at = model.get("created_at")
        if best is None or (created_at and created_at > best[0]):
            best = (created_at, project.id)

    return best[1] if best else None


def _get_azure_cosmos_line_item(client, project_id: str) -> dict[str, Any] | None:
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

    azure = (
        runs[0]
        .reference.collection(FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION)
        .document("azure")
        .get()
    )
    if not azure.exists:
        return None

    data = azure.to_dict() or {}
    for item in data.get("line_items") or []:
        if item.get("service_id") == "azure_cosmos_db":
            return item
    return None


def _select_sku(
    *,
    capacity_mode: Any,
    skus: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    from app.config.params import COSMOS_DB_CAPACITY_MODES

    if isinstance(capacity_mode, (int, float)):
        raise ValueError("capacity_mode must be a string enum, not a number.")
    if capacity_mode not in COSMOS_DB_CAPACITY_MODES:
        allowed = ", ".join(sorted(COSMOS_DB_CAPACITY_MODES))
        raise ValueError(f"capacity_mode must be one of: {allowed}.")

    selected = next(sku for sku in skus if sku.get("name") == capacity_mode)
    return selected, "matched capacity_mode input"


def _price_field_issues(sku: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    mode = sku.get("name", "")
    fields = (
        SERVERLESS_PRICE_FIELDS
        if mode == "Serverless"
        else PROVISIONED_PRICE_FIELDS
    )
    for field in fields:
        value = sku.get(field)
        if value is None:
            issues.append(f"{field} is null")
        elif isinstance(value, (int, float)) and value == 0:
            issues.append(f"{field} is zero")
    return issues


def _throughput_free_tier_applies(sku_name: str) -> bool:
    return sku_name in {"Provisioned Throughput", "Autoscale"}


def debug_project(project_id: str) -> int:
    client = get_firestore_client()
    pricing_repo = PricingServiceRepository(client)
    mapping_repo = CloudServiceMappingRepository(client)

    project_ref = client.collection(FIRESTORE_PROJECTS_COLLECTION).document(project_id)
    if not project_ref.get().exists:
        print(f"Project not found: {project_id}")
        return 1

    selection_docs = list(
        project_ref.collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    selection_id = selection_docs[0].id if selection_docs else None

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

    pricing_service = pricing_repo.find_by_id("azure_cosmos_db")
    if pricing_service is None:
        print("azure_cosmos_db pricing service not found in Firestore")
        return 1

    skus = pricing_service.get("skus") or []
    script = pricing_service.get("script_calculation", "")
    free_tier = pricing_service.get("free_tier") or {}

    capacity_mode = usage_inputs.get("capacity_mode")
    if capacity_mode is None:
        print("ERROR: capacity_mode is missing from usage inputs.")
        return 1
    request_units_per_month = max(0, float(usage_inputs.get("request_units_per_month", 0) or 0))
    required_ru_per_second = max(0, float(usage_inputs.get("required_ru_per_second", 0) or 0))
    database_storage_gb = max(0, float(usage_inputs.get("database_storage_gb", 0) or 0))

    try:
        selected_sku, selection_reason = _select_sku(capacity_mode=capacity_mode, skus=skus)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 1
    sku_name = selected_sku.get("name", "")

    free_storage_gb = float(free_tier.get("database_storage_gb", 0) or 0)
    billable_storage_gb = max(0, database_storage_gb - free_storage_gb)
    storage_price_per_gb = selected_sku.get("storage_price_per_gb_month")
    storage_cost = billable_storage_gb * float(storage_price_per_gb or 0)

    free_ru_per_second = float(free_tier.get("throughput_ru_per_second", 0) or 0)
    throughput_free_applies = _throughput_free_tier_applies(sku_name)
    billable_ru_per_second = (
        max(0, required_ru_per_second - free_ru_per_second)
        if throughput_free_applies
        else required_ru_per_second
    )

    print(f"Project: {project_id}")
    print(f"Selection: {selection_id}")
    print(f"Usage model: {usage_document['id']}")
    print(f"Usage model selection_id: {usage_document.get('selection_id')}")
    print(f"Stale: {usage_document.get('stale', False)}")
    print()

    mapping = mapping_repo.find_by_id("nosql_database")
    if mapping:
        azure_services = (mapping.get("providers") or {}).get("azure") or []
        print("Azure mapping for nosql_database:")
        for entry in azure_services:
            print(f"  - {entry}")
        print()

    print("LLM values in usage model:")
    for param in COSMOS_LLM_PARAMS:
        estimate = payload.llm.get(param)
        if estimate:
            print(f"  {param}: {estimate.value!r} (reason: {estimate.reason})")
        else:
            print(f"  {param}: <missing>")
    print()

    print("Flat usage_inputs passed to calculate_price():")
    for key in sorted(usage_inputs):
        if key in COSMOS_LLM_PARAMS or key in {"users", "request_units_per_month"}:
            print(f"  {key}: {usage_inputs[key]!r}")
    print()

    print("Cosmos DB pricing inputs:")
    print(f"  capacity_mode: {capacity_mode!r}")
    print(f"  request_units_per_month: {request_units_per_month}")
    print(f"  required_ru_per_second: {required_ru_per_second}")
    print(f"  database_storage_gb: {database_storage_gb}")
    print()

    print("Available SKUs:")
    for sku in skus:
        print(f"  - {sku}")
    print()

    print("Selected SKU:")
    print(f"  name: {sku_name}")
    print(f"  reason: {selection_reason}")
    print(f"  full record: {selected_sku}")
    print()

    print("SKU unit prices:")
    for field in sorted(selected_sku):
        if field != "name":
            value = selected_sku.get(field)
            flag = ""
            if value is None:
                flag = "  <-- NULL"
            elif isinstance(value, (int, float)) and value == 0:
                flag = "  <-- ZERO"
            print(f"  {field}: {value!r}{flag}")
    print()

    price_issues = _price_field_issues(selected_sku)
    if price_issues:
        print("Price field verification: FAILED")
        for issue in price_issues:
            print(f"  - {issue}")
    else:
        print("Price field verification: required price fields are present and non-zero")
    print()

    print("Configured free tier:")
    for key, value in free_tier.items():
        print(f"  {key}: {value}")
    print()

    print("Free tier applicability for selected mode:")
    print(
        f"  storage free tier ({free_storage_gb} GB): applies to all modes; "
        f"usage {database_storage_gb} GB -> billable {billable_storage_gb} GB"
    )
    if throughput_free_applies:
        print(
            f"  throughput free tier ({free_ru_per_second} RU/s): applies to {sku_name}; "
            f"usage {required_ru_per_second} RU/s -> billable {billable_ru_per_second} RU/s"
        )
    else:
        print(
            f"  throughput free tier ({free_ru_per_second} RU/s): does NOT apply to Serverless; "
            f"request RUs are billed without throughput free tier"
        )
    print()

    print("Billable usage:")
    print(f"  billable storage (GB): {billable_storage_gb}")
    if sku_name == "Serverless":
        print(f"  billable request units (month): {request_units_per_month}")
        print(f"  billable RU/s (provisioned path): n/a for Serverless")
    else:
        print(f"  billable request units (month): n/a for {sku_name}")
        print(f"  billable RU/s: {billable_ru_per_second}")
    print()

    print("Final calculation:")
    if sku_name == "Serverless":
        price_per_million_ru = selected_sku.get("price_per_million_ru")
        if price_per_million_ru is None:
            price_per_million_ru = 0.25
            print("  price_per_million_ru was null; script default 0.25 applied")
        request_cost = (request_units_per_month / 1_000_000) * float(price_per_million_ru)
        estimated_price = request_cost + storage_cost
        print(f"  request_cost = ({request_units_per_month} / 1_000_000) * {price_per_million_ru}")
        print(f"               = ${request_cost:.4f}")
        print(
            f"  storage_cost = {billable_storage_gb} GB * ${storage_price_per_gb}/GB"
        )
        print(f"               = ${storage_cost:.4f}")
        print(f"  monthly_total = ${round(estimated_price, 2):.2f}")
        if estimated_price == 0:
            print(
                "  note: $0 only if request_units_per_month is 0 and storage is within free tier"
            )
    else:
        throughput_unit = float(selected_sku.get("throughput_unit_ru_per_second") or 0)
        price_per_100_ru_hour = float(selected_sku.get("price_per_100_ru_hour") or 0)
        throughput_units = (
            math.ceil(billable_ru_per_second / throughput_unit) if throughput_unit else 0
        )
        throughput_cost = throughput_units * price_per_100_ru_hour * 730
        estimated_price = throughput_cost + storage_cost
        print(
            f"  throughput_units = ceil({billable_ru_per_second} / {throughput_unit})"
            f" = {throughput_units}"
        )
        print(
            f"  throughput_cost = {throughput_units} * ${price_per_100_ru_hour}"
            f" * 730 hours = ${throughput_cost:.4f}"
        )
        print(
            f"  storage_cost = {billable_storage_gb} GB * ${storage_price_per_gb}/GB"
            f" = ${storage_cost:.4f}"
        )
        print(f"  monthly_total = ${round(estimated_price, 2):.2f}")
        if estimated_price == 0:
            print(
                "  note: $0 only if throughput and storage are fully covered by applicable free tiers"
            )
    print()

    script_price = execute_pricing_script(
        script,
        inputs=usage_inputs,
        skus=skus,
        free_tier=free_tier,
    ).monthly_price
    print(f"Script calculate_price() result: ${script_price}")

    line_item = _get_azure_cosmos_line_item(client, project_id)
    if line_item:
        print()
        print("Stored Azure pricing line item:")
        print(f"  component: {line_item.get('component_name')}")
        print(f"  service: {line_item.get('service_name')}")
        print(f"  monthly_price: ${line_item.get('monthly_price')}")
    else:
        print()
        print("No stored azure_cosmos_db line item found for the latest Azure pricing run.")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project_id",
        nargs="?",
        help="Firestore project id (defaults to latest project with Cosmos DB LLM values)",
    )
    args = parser.parse_args(argv)

    project_id = args.project_id
    if not project_id:
        client = get_firestore_client()
        project_id = _find_latest_project_with_cosmos_params(client)
        if not project_id:
            print("No project with Cosmos DB LLM values found.")
            return 1
        print(f"Using latest project with Cosmos DB values: {project_id}\n")

    return debug_project(project_id)


if __name__ == "__main__":
    raise SystemExit(main())
