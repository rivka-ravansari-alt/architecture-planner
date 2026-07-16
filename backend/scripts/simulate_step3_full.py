"""Full Step 3 simulation for two distinct projects.

Runs the complete global usage model pipeline with seed-aligned mappings and
pricing metadata. Prints every intermediate artifact for inspection.

Run from the backend directory (reads OPENAI_API_KEY from .env):

    python scripts/simulate_step3_full.py
"""

from __future__ import annotations

import json
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.ai_client import AIClientFactory
from app.core.exceptions import AIClientError, AIValidationError
from app.schemas.global_usage_model import GlobalUsageModelPayload
from app.services.global_usage_prompt_builder import GlobalUsagePromptBuilder
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_parameter_resolver import UsageParameterResolver
from app.validators.global_usage_validator import parse_and_validate
from scripts.seed_cloud_service_mappings import MAPPINGS
from scripts.seed_pricing_services import PRICING_SERVICES


@dataclass
class SimulationProject:
    key: str
    title: str
    application_description: str
    platform: str
    stage: str
    expected_users: int
    requirements: dict[str, Any]
    selected_components: list[dict[str, Any]]


PROJECTS: list[SimulationProject] = [
    SimulationProject(
        key="simple_crud_saas",
        title="Team Task Manager (CRUD SaaS)",
        application_description=(
            "A simple team task-management SaaS. Users sign in, create projects and "
            "tasks, assign them to teammates, and track status on a kanban board. "
            "Standard CRUD over relational data with user accounts. No file uploads, "
            "no AI, no payments, no real-time features."
        ),
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={
            "authentication": {"enabled": True},
            "file_uploads": {"enabled": False},
            "background_processing": {"enabled": False},
            "dashboards_reports": {"enabled": False},
            "ai_usage": {"enabled": False},
            "payments": {"enabled": False},
            "realtime": {"enabled": False},
        },
        selected_components=[
            {
                "category_id": "compute",
                "name": "Compute",
                "description": "Runs application code, APIs, and background jobs.",
                "reason": "Needed to serve REST APIs and business logic.",
            },
            {
                "category_id": "api",
                "name": "API Gateway",
                "description": "Secure API entry point.",
                "reason": "Web clients call backend APIs through a gateway.",
            },
            {
                "category_id": "authentication",
                "name": "Authentication",
                "description": "User authentication and access control.",
                "reason": "Users must sign in to manage tasks.",
            },
            {
                "category_id": "sql_database",
                "name": "SQL Database",
                "description": "Relational data store.",
                "reason": "Tasks, projects, and assignments are relational.",
            },
        ],
    ),
    SimulationProject(
        key="ai_document_assistant",
        title="AI Document Assistant (RAG + uploads)",
        application_description=(
            "An AI document assistant for legal teams. Users upload PDF contracts, "
            "the system extracts text asynchronously, embeds documents, and answers "
            "natural-language questions with retrieval-augmented generation. Chat "
            "history is stored per user. High read volume on stored documents."
        ),
        platform="web",
        stage="production",
        expected_users=50000,
        requirements={
            "authentication": {"enabled": True},
            "file_uploads": {
                "enabled": True,
                "files_per_month": "10000-100000",
                "average_file_size": "1-10mb",
            },
            "background_processing": {"enabled": True},
            "ai_usage": {
                "enabled": True,
                "ai_type": "document_processing",
                "usage_frequency": "high",
            },
            "dashboards_reports": {"enabled": False},
            "payments": {"enabled": False},
            "realtime": {"enabled": True, "features": ["chat"]},
        },
        selected_components=[
            {
                "category_id": "compute",
                "name": "Compute",
                "description": "Runs application code and async workers.",
                "reason": "Serves APIs and document processing workers.",
            },
            {
                "category_id": "api",
                "name": "API Gateway",
                "description": "Secure API entry point.",
                "reason": "Chat and upload APIs enter through a gateway.",
            },
            {
                "category_id": "authentication",
                "name": "Authentication",
                "description": "User authentication.",
                "reason": "Each legal team member has their own account.",
            },
            {
                "category_id": "storage",
                "name": "Object Storage",
                "description": "Stores uploaded PDFs and extracted assets.",
                "reason": "Contract PDFs and generated thumbnails are stored as objects.",
            },
            {
                "category_id": "queue",
                "name": "Message Queue",
                "description": "Async job queue.",
                "reason": "Document parsing and embedding run asynchronously.",
            },
            {
                "category_id": "nosql_database",
                "name": "NoSQL Database",
                "description": "Flexible document/chat store.",
                "reason": "Chat sessions and embedding metadata fit a document model.",
            },
            {
                "category_id": "ai_llm",
                "name": "AI / LLM",
                "description": "LLM inference and embeddings.",
                "reason": "Powers Q&A and retrieval over uploaded contracts.",
            },
            {
                "category_id": "cache",
                "name": "Cache",
                "description": "In-memory cache.",
                "reason": "Caches frequent retrieval results and session context.",
            },
        ],
    ),
]


class SeedMappingRepository:
    def __init__(self) -> None:
        self._mappings = {item["category_id"]: item for item in MAPPINGS}

    def find_by_id(self, category_id: str):
        return self._mappings.get(category_id)


class SeedPricingRepository:
    def __init__(self) -> None:
        self._services = {
            item["service_id"]: item for item in PRICING_SERVICES if "service_id" in item
        }

    def find_by_id(self, service_id: str):
        return self._services.get(service_id)


def _section(title: str) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def _print_json(label: str, payload: Any) -> None:
    print(f"\n{label}:")
    print(json.dumps(payload, indent=2, sort_keys=True))


def _print_prompt(prompt: str) -> None:
    print("\nFinal prompt:")
    print("```")
    print(prompt)
    print("```")


def _print_usage_model(payload: GlobalUsageModelPayload) -> None:
    model = {
        "llm": {
            name: {"value": estimate.value, "reason": estimate.reason}
            for name, estimate in sorted(payload.llm.items())
        },
        "static": dict(sorted(payload.static.items())),
    }
    _print_json("Validated usage model", model)


def run_project(project: SimulationProject, ai_client) -> int:
    print("\n" + "=" * 78)
    print(f"PROJECT: {project.key} — {project.title}")
    print("=" * 78)

    _section("Project summary")
    print(textwrap.fill(project.application_description, width=76))
    print(f"Stage: {project.stage}")
    print(f"Expected users: {project.expected_users}")
    _print_json("Requirements", project.requirements)

    _section("Selected components")
    for component in project.selected_components:
        print(
            f"  - {component['category_id']} ({component['name']}): "
            f"{component['reason']}"
        )

    resolver = UsageParameterResolver(SeedMappingRepository(), SeedPricingRepository())
    resolved = resolver.resolve_for_selected_components(project.selected_components)

    _section("Required parameters")
    print("LLM parameters (to_know.llm):")
    for name in resolved.llm:
        print(f"  - {name}")
    if not resolved.llm:
        print("  (none)")

    print("\nStatic parameters (to_know.static + global):")
    for name in resolved.static:
        print(f"  - {name}")
    if not resolved.static:
        print("  (none)")

    static_values = StaticUsageValueResolver().resolve(
        resolved.static,
        expected_users=project.expected_users,
        stage=project.stage,
        requirements=project.requirements,
    )
    _print_json("Resolved static values (not sent to OpenAI)", static_values)

    llm_usage: dict[str, Any] = {}
    raw_response = ""

    if resolved.llm:
        prompt_builder = GlobalUsagePromptBuilder()
        prompt = prompt_builder.build(
            application_description=project.application_description,
            platform=project.platform,
            stage=project.stage,
            expected_users=project.expected_users,
            requirements=project.requirements,
            selected_components=project.selected_components,
            usage_parameters=resolved.llm,
        )
        _section("Prompt")
        _print_prompt(prompt)

        _section("OpenAI call")
        started = time.perf_counter()
        try:
            raw_response = ai_client.generate(prompt)
        except AIClientError as error:
            print(f"AI CLIENT ERROR: {error}")
            return 2
        elapsed = time.perf_counter() - started
        print(f"Completed in {elapsed:.1f}s")

        print("\nRaw OpenAI response:")
        print("```")
        print(raw_response)
        print("```")

        _section("Validation")
        try:
            llm_result = parse_and_validate(raw_response, resolved.llm)
        except AIValidationError as error:
            print(f"VALIDATION FAILED: {error.message}")
            return 1
        print("Validation passed.")
        llm_usage = llm_result.usage
    else:
        print("\nNo LLM parameters required — skipping OpenAI call.")

    payload = GlobalUsageModelPayload(llm=llm_usage, static=static_values)
    _section("Complete usage model")
    _print_usage_model(payload)
    return 0


def main() -> int:
    print("=" * 78)
    print("STEP 3 FULL SIMULATION — two projects")
    print(f"Mappings: {len(MAPPINGS)} categories | Pricing services: {len(PRICING_SERVICES)}")
    print("=" * 78)

    try:
        ai_client = AIClientFactory.create()
    except AIClientError as error:
        print(f"FATAL: could not create AI client: {error}")
        return 2
    print(f"AI client: {type(ai_client).__name__}")

    exit_code = 0
    for index, project in enumerate(PROJECTS, start=1):
        print(f"\n>>> Running project {index}/{len(PROJECTS)}")
        result = run_project(project, ai_client)
        if result != 0:
            exit_code = result

    print("\n" + "=" * 78)
    print("SIMULATION COMPLETE")
    print("=" * 78)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
