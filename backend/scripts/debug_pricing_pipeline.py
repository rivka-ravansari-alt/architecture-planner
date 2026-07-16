"""Debug why selected components are missing from pricing results."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from app.clients.firestore_client import get_firestore_client
from app.config.params import (
    FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION,
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PRICING_RUNS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
    FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION,
    PRICING_GENERATION_ORDER,
)
from app.repositories.cloud_service_mapping_repository import CloudServiceMappingRepository
from app.repositories.pricing_service_repository import PricingServiceRepository
from app.schemas.global_usage_model import GlobalUsageModelPayload, UsageParameterEstimate
from app.services.pricing_calculation_executor import (
    PricingCalculationError,
    execute_pricing_script,
)
from app.services.usage_inputs_builder import build_usage_inputs
from app.validators.usage_inputs_validator import validate_service_inputs


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


def _resolve_service_for_component(
    *,
    mapping_repo: CloudServiceMappingRepository,
    pricing_repo: PricingServiceRepository,
    category_id: str,
    provider: str,
) -> tuple[dict[str, Any] | None, str | None]:
    mapping = mapping_repo.find_by_id(category_id)
    if mapping is None:
        return None, f"No cloud_service_mapping document for category_id '{category_id}'."

    providers = mapping.get("providers") or {}
    if not isinstance(providers, dict):
        return None, f"Mapping for '{category_id}' has invalid providers field."

    provider_services = providers.get(provider)
    if not isinstance(provider_services, list) or not provider_services:
        return None, f"No {provider.upper()} services mapped for category_id '{category_id}'."

    sorted_services = sorted(
        (
            entry
            for entry in provider_services
            if isinstance(entry, dict) and entry.get("service_id")
        ),
        key=lambda entry: int(entry.get("priority", 999)),
    )
    if not sorted_services:
        return None, f"No valid service entries for {provider.upper()} on '{category_id}'."

    missing: list[str] = []
    for entry in sorted_services:
        service_id = str(entry["service_id"]).strip()
        if pricing_repo.find_by_id(service_id) is not None:
            return {**entry, "service_id": service_id}, None
        missing.append(service_id)

    return None, (
        f"Mapped {provider.upper()} services exist ({', '.join(missing)}) "
        f"but none have a pricing_services document."
    )


def _find_latest_project(client) -> str | None:
    for snapshot in client.collection(FIRESTORE_PROJECTS_COLLECTION).stream():
        selections = list(
            snapshot.reference.collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
            .order_by("created_at", direction="DESCENDING")
            .limit(1)
            .stream()
        )
        if selections:
            return snapshot.id
    return None


def _stored_line_items(client, project_id: str, provider: str) -> dict[str, dict[str, Any]]:
    runs = list(
        client.collection(FIRESTORE_PROJECTS_COLLECTION)
        .document(project_id)
        .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    if not runs:
        return {}

    result_doc = (
        runs[0]
        .reference.collection(FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION)
        .document(provider)
        .get()
    )
    if not result_doc.exists:
        return {}

    data = result_doc.to_dict() or {}
    return {
        item.get("instance_id"): item
        for item in data.get("line_items") or []
        if item.get("instance_id")
    }


def debug_project(project_id: str) -> int:
    client = get_firestore_client()
    mapping_repo = CloudServiceMappingRepository(client)
    pricing_repo = PricingServiceRepository(client)

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
    if not selection_docs:
        print(f"No architecture selection for project {project_id}")
        return 1

    selection = selection_docs[0].to_dict() or {}
    selected = list(selection.get("selected", []))

    usage_docs = list(
        project_ref.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    usage_inputs: dict[str, Any] = {}
    if usage_docs:
        usage_document = usage_docs[0].to_dict() or {}
        payload = _usage_payload_from_document(usage_document)
        usage_inputs = build_usage_inputs(payload)

    print(f"Project: {project_id}")
    print(f"Selection: {selection_docs[0].id}")
    print(f"Selected components: {len(selected)}")
    print()

    for index, component in enumerate(selected, start=1):
        instance_id = component.get("instance_id") or component.get("uid")
        category_id = component.get("category_id") or component.get("id")
        name = component.get("name") or category_id or "<unknown>"

        print(f"{'=' * 72}")
        print(f"{index}. {name}")
        print(f"   instance_id: {instance_id or '<missing>'}")
        print(f"   category_id: {category_id or '<missing>'}")

        if not instance_id or not category_id:
            print("   STATUS: SKIPPED")
            print("   REASON: Missing instance_id or category_id on the selection record.")
            print()
            continue

        for provider in PRICING_GENERATION_ORDER:
            stored = _stored_line_items(client, project_id, provider)
            stored_item = stored.get(instance_id)

            print(f"   --- {provider.upper()} ---")
            service_entry, skip_reason = _resolve_service_for_component(
                mapping_repo=mapping_repo,
                pricing_repo=pricing_repo,
                category_id=category_id,
                provider=provider,
            )

            if service_entry is None:
                print(f"   mapped service: none")
                print(f"   pricing_service exists: no")
                print(f"   pricing executed: no")
                print(f"   skip reason: {skip_reason}")
                if stored_item:
                    print(
                        f"   stored line item: unexpected entry found "
                        f"(${stored_item.get('monthly_price')})"
                    )
                continue

            service_id = service_entry["service_id"]
            pricing_service = pricing_repo.find_by_id(service_id)
            has_pricing = pricing_service is not None
            has_script = bool(pricing_service and pricing_service.get("script_calculation"))

            print(f"   mapped service: {service_id} (priority {service_entry.get('priority', '?')})")
            print(f"   pricing_service exists: {'yes' if has_pricing else 'no'}")
            if has_pricing:
                print(f"   script_calculation present: {'yes' if has_script else 'no'}")

            if not has_pricing:
                print(f"   pricing executed: no")
                print(
                    f"   skip reason: pricing_services/{service_id} document is missing "
                    f"in Firestore."
                )
                continue

            if not has_script:
                print(f"   pricing executed: no")
                print(f"   skip reason: pricing service '{service_id}' has no script_calculation.")
                continue

            try:
                if usage_inputs:
                    validate_service_inputs(service_id, usage_inputs)
                execute_pricing_script(
                    pricing_service.get("script_calculation", ""),
                    inputs=usage_inputs,
                    skus=pricing_service.get("skus") or [],
                    free_tier=pricing_service.get("free_tier") or {},
                )
                executed = True
                exec_error = None
            except PricingCalculationError as error:
                executed = False
                exec_error = str(error)

            if stored_item:
                print(f"   pricing executed: yes (stored ${stored_item.get('monthly_price')})")
            elif executed:
                print(f"   pricing executed: yes (dry-run succeeded)")
            else:
                print(f"   pricing executed: no")
                print(f"   skip reason: script failed: {exec_error}")

        print()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", nargs="?", help="Firestore project id")
    args = parser.parse_args(argv)

    project_id = args.project_id
    if not project_id:
        client = get_firestore_client()
        project_id = _find_latest_project(client)
        if not project_id:
            print("No project with an architecture selection found.")
            return 1
        print(f"Using latest project: {project_id}\n")

    return debug_project(project_id)


if __name__ == "__main__":
    raise SystemExit(main())
