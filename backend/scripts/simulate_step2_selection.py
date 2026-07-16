"""Simulation harness for Step 2 (architecture component category selection).

Runs the real Step 2 LLM flow (``ArchitectureComponentSelectionService.select``)
against several application scenarios, using the same 15 architecture categories
that ``seed_architecture_categories.py`` writes to Firestore. It does NOT touch
Firestore or HTTP -- it exercises the prompt builder, the OpenAI client, and the
Step 2 validator in isolation so we can inspect whether the LLM output is "ok".

For each scenario it reports:
  * whether the response passed the hard Step 2 validator (JSON shape, full
    coverage of every category exactly once, no unknown/duplicate ids), and
  * soft "sanity" expectations for the scenario (e.g. an AI chat app should
    select the ai_llm category). Sanity failures are warnings, not hard errors.

Run from the backend directory (reads OPENAI_API_KEY from .env):

    python scripts/simulate_step2_selection.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.ai_client import AIClientFactory
from app.core.exceptions import AIClientError, AIValidationError
from app.schemas.component_selection import ComponentSelectionResult
from app.services.architecture_component_selection_service import (
    ArchitectureComponentSelectionService,
)

# The canonical 15 categories (kept in sync with seed_architecture_categories.py).
# Copied here so the simulation stays isolated from Firestore.
CATEGORIES: list[dict[str, str]] = [
    {"id": "compute", "name": "Compute", "description": "Runs application code, APIs, containers, serverless functions, and background processing."},
    {"id": "workflow", "name": "Workflow", "description": "Orchestrates multi-step processes, business workflows, retries, approvals, and long-running tasks."},
    {"id": "api", "name": "API Gateway", "description": "Provides a secure entry point for APIs, handling routing, authentication, rate limiting, and request management."},
    {"id": "authentication", "name": "Authentication", "description": "Manages user authentication, authorization, identity providers, OAuth, SSO, and access control."},
    {"id": "sql_database", "name": "SQL Database", "description": "Stores structured relational data using tables, transactions, and SQL queries with strong consistency."},
    {"id": "nosql_database", "name": "NoSQL Database", "description": "Stores flexible, schema-less data such as documents, key-value pairs, or wide-column records with high scalability."},
    {"id": "storage", "name": "Object Storage", "description": "Stores files and binary objects such as images, videos, documents, backups, and generated content."},
    {"id": "cache", "name": "Cache", "description": "Stores frequently accessed data in memory to reduce latency and improve application performance."},
    {"id": "queue", "name": "Message Queue", "description": "Enables asynchronous communication between services by buffering and delivering messages reliably."},
    {"id": "events", "name": "Event Bus", "description": "Distributes events between services using an event-driven architecture, allowing systems to react to changes asynchronously."},
    {"id": "notification", "name": "Notification Service", "description": "Delivers notifications to users through channels such as email, SMS, push notifications, or in-app messaging."},
    {"id": "scheduler", "name": "Scheduler", "description": "Runs tasks automatically at scheduled times or recurring intervals, such as cron jobs and maintenance tasks."},
    {"id": "ai_llm", "name": "AI / LLM", "description": "Provides access to AI models for chat, text generation, summarization, image analysis, embeddings, and other intelligent features."},
    {"id": "monitoring", "name": "Monitoring", "description": "Collects metrics, logs, traces, and health information to monitor system performance and reliability."},
    {"id": "analytics", "name": "Analytics", "description": "Processes and analyzes application data to generate reports, dashboards, business insights, and large-scale queries."},
]

ALL_IDS = {c["id"] for c in CATEGORIES}


@dataclass
class Scenario:
    key: str
    application_description: str
    platform: str
    stage: str
    expected_users: int
    requirements: dict[str, Any]
    # Soft expectations: ids we expect selected / excluded for a sensible answer.
    expect_selected: set[str] = field(default_factory=set)
    expect_excluded: set[str] = field(default_factory=set)


SCENARIOS: list[Scenario] = [
    Scenario(
        key="simple_crud_saas",
        application_description=(
            "A simple team task-management SaaS. Users sign in, create projects and "
            "tasks, assign them to teammates, and track status on a board. Standard "
            "CRUD over relational data with user accounts. No file uploads, no AI, no "
            "payments."
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
        expect_selected={"compute", "api", "authentication", "sql_database"},
        expect_excluded={"ai_llm"},
    ),
    Scenario(
        key="ai_chat_assistant",
        application_description=(
            "An AI chat assistant web app. Users chat with an LLM, the app streams "
            "responses in real time, keeps conversation history, and does retrieval "
            "over uploaded documents using embeddings. High traffic, needs low latency."
        ),
        platform="web",
        stage="production",
        expected_users=100000,
        requirements={
            "authentication": {"enabled": True},
            "file_uploads": {"enabled": True, "files_per_month": "10000-100000", "average_file_size": "1-10mb"},
            "background_processing": {"enabled": True},
            "ai_usage": {"enabled": True, "features": ["chat", "embeddings", "rag"]},
            "realtime": {"enabled": True},
            "dashboards_reports": {"enabled": False},
            "payments": {"enabled": False},
        },
        expect_selected={"compute", "api", "authentication", "ai_llm", "storage", "cache"},
        expect_excluded=set(),
    ),
    Scenario(
        key="ecommerce_platform",
        application_description=(
            "An e-commerce platform. Product catalog, shopping cart, checkout with "
            "online payments, order processing, inventory, email/SMS notifications for "
            "order status, and an admin analytics dashboard for sales. Product images "
            "are uploaded and served."
        ),
        platform="web",
        stage="production",
        expected_users=50000,
        requirements={
            "authentication": {"enabled": True},
            "file_uploads": {"enabled": True, "files_per_month": "1000-10000", "average_file_size": "100kb-1mb"},
            "background_processing": {"enabled": True},
            "dashboards_reports": {"enabled": True, "features": ["dashboard", "reports"]},
            "payments": {"enabled": True},
            "external_integrations": {"enabled": True, "services": ["payment_gateway"]},
            "ai_usage": {"enabled": False},
            "realtime": {"enabled": False},
        },
        expect_selected={"compute", "api", "authentication", "sql_database", "storage", "notification", "analytics"},
        expect_excluded={"ai_llm"},
    ),
    Scenario(
        key="video_processing_pipeline",
        application_description=(
            "A video upload and processing platform. Creators upload large video files, "
            "the system transcodes them into multiple resolutions asynchronously, "
            "generates thumbnails, and notifies the creator when processing completes. "
            "Videos are stored and streamed to viewers. Scheduled cleanup of temp files."
        ),
        platform="web",
        stage="production",
        expected_users=20000,
        requirements={
            "authentication": {"enabled": True},
            "file_uploads": {"enabled": True, "files_per_month": "10000-100000", "average_file_size": "100mb-1gb"},
            "background_processing": {"enabled": True},
            "ai_usage": {"enabled": False},
            "payments": {"enabled": False},
            "realtime": {"enabled": False},
            "dashboards_reports": {"enabled": False},
        },
        expect_selected={"compute", "api", "authentication", "storage", "queue", "notification"},
        expect_excluded=set(),
    ),
]


# Phrases that indicate a category is NOT wanted. If one of these shows up in a
# reason for a SELECTED item (or the inverse for an EXCLUDED item), the model
# contradicted itself -- the bucket and the justification disagree.
_NEGATIVE_REASON_MARKERS = (
    "not needed",
    "not necessary",
    "not required",
    "not applicable",
    "no need",
    "isn't needed",
    "is not needed",
    "not enabled",
    "not used",
)


def _check_reason_contradictions(result: ComponentSelectionResult) -> list[str]:
    """Flag decisions whose reason text contradicts the bucket it was placed in.

    The structural validator only checks coverage/uniqueness; it cannot tell that
    an item placed in ``selected`` with a reason saying "not needed" is wrong.
    """

    problems: list[str] = []
    for item in result.selected:
        lowered = item.reason.lower()
        if any(marker in lowered for marker in _NEGATIVE_REASON_MARKERS):
            problems.append(
                f"'{item.id}' is SELECTED but its reason implies it is not needed: "
                f"\"{item.reason}\""
            )
    return problems


def _check_soft_expectations(
    result: ComponentSelectionResult, scenario: Scenario
) -> list[str]:
    selected_ids = {item.id for item in result.selected}
    excluded_ids = {item.id for item in result.excluded}
    warnings: list[str] = []

    for expected in sorted(scenario.expect_selected):
        if expected not in selected_ids:
            where = "excluded" if expected in excluded_ids else "missing"
            warnings.append(f"expected '{expected}' to be SELECTED but it was {where}")
    for expected in sorted(scenario.expect_excluded):
        if expected not in excluded_ids:
            where = "selected" if expected in selected_ids else "missing"
            warnings.append(f"expected '{expected}' to be EXCLUDED but it was {where}")
    return warnings


def _print_result(scenario: Scenario, result: ComponentSelectionResult) -> None:
    print(f"    selected ({len(result.selected)}):")
    for item in result.selected:
        print(f"      + {item.id}: {item.reason}")
    print(f"    excluded ({len(result.excluded)}):")
    for item in result.excluded:
        print(f"      - {item.id}: {item.reason}")


def main() -> int:
    print("=" * 78)
    print("STEP 2 SIMULATION - architecture component category selection")
    print(f"Scenarios: {len(SCENARIOS)} | Categories: {len(CATEGORIES)}")
    print("=" * 78)

    try:
        ai_client = AIClientFactory.create()
    except AIClientError as error:
        print(f"FATAL: could not create AI client: {error}")
        return 2
    print(f"AI client: {type(ai_client).__name__}")

    service = ArchitectureComponentSelectionService(ai_client)

    hard_pass = 0
    hard_fail = 0
    sanity_clean = 0
    contradiction_free = 0

    for index, scenario in enumerate(SCENARIOS, start=1):
        print("\n" + "-" * 78)
        print(f"[{index}/{len(SCENARIOS)}] scenario: {scenario.key}")
        print(f"    stage={scenario.stage} expected_users={scenario.expected_users}")
        started = time.perf_counter()
        try:
            result = service.select(
                application_description=scenario.application_description,
                platform=scenario.platform,
                stage=scenario.stage,
                expected_users=scenario.expected_users,
                requirements=scenario.requirements,
                categories=CATEGORIES,
            )
        except AIValidationError as error:
            hard_fail += 1
            elapsed = time.perf_counter() - started
            print(f"    HARD VALIDATION FAILED after {elapsed:.1f}s: {error.message}")
            continue
        except AIClientError as error:
            hard_fail += 1
            elapsed = time.perf_counter() - started
            print(f"    AI CLIENT ERROR after {elapsed:.1f}s: {error}")
            continue

        elapsed = time.perf_counter() - started
        hard_pass += 1

        # The service already ran parse_and_validate; re-assert coverage here so
        # the report is self-contained and explicit about what "ok" means.
        covered = {i.id for i in result.selected} | {i.id for i in result.excluded}
        coverage_ok = covered == ALL_IDS
        print(f"    HARD VALIDATION PASSED in {elapsed:.1f}s (coverage_ok={coverage_ok})")
        _print_result(scenario, result)

        contradictions = _check_reason_contradictions(result)
        if contradictions:
            print("    REASON CONTRADICTIONS (bucket disagrees with justification):")
            for problem in contradictions:
                print(f"      x {problem}")
        else:
            contradiction_free += 1
            print("    REASON CONSISTENCY: no bucket/justification contradictions")

        warnings = _check_soft_expectations(result, scenario)
        if warnings:
            print("    SANITY WARNINGS:")
            for warning in warnings:
                print(f"      ! {warning}")
        else:
            sanity_clean += 1
            print("    SANITY CHECKS: all expectations met")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print(f"  hard validation passed : {hard_pass}/{len(SCENARIOS)}")
    print(f"  hard validation failed : {hard_fail}/{len(SCENARIOS)}")
    print(f"  reason-consistent      : {contradiction_free}/{len(SCENARIOS)}")
    print(f"  sanity checks clean    : {sanity_clean}/{len(SCENARIOS)}")
    print("=" * 78)

    return 0 if hard_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
