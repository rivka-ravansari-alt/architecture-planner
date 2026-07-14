"""Local in-process runner for PyCharm debugging.

Calls controllers/services directly — no HTTP, no uvicorn, no TestClient.
By default uses OpenAI from .env. Set use_mock_ai=true for a fixed test
response without calling OpenAI.

Run/debug this file from PyCharm with working directory = backend/.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy.orm import Session

from app.api.controllers.health_controller import HealthController
from app.api.controllers.project_controller import ProjectController
from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.core.database import SessionLocal, init_db
from app.models import User
from app.schemas.project import ComponentsUpdate, ProjectCreate, ProjectDetail
from app.services.catalog_service import CatalogService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hardcoded input — edit this before running / debugging.
# ---------------------------------------------------------------------------
EVENT: dict[str, Any] = {
    # True  = fixed test JSON (no remote OpenAI)
    # False = real OpenAI call from .env (default)
    "use_mock_ai": False,
    "user": {
        "google_sub": "113189359163347349625",
        "email": "rivka.ravansari@gmail.com",
        "name": "Rivka Ravansari",
    },
    # Leave None to create a new project from project_create; set to reuse one.
    "project_id": "492aedca-fa6f-4e65-bd6d-c52c901b3f62",
    "project_create": {
        "name": "TaskFlow",
        "description": (
            "A team task management product with user auth, projects, "
            "and real-time collaboration."
        ),
        "project_types": ["web_app"],
        "stage": "mvp",
        "expected_users": "1000",
        "answers": {
            "auth": True,
            "file_upload": True,
            "background_processing": False,
            "dashboards": True,
            "ai": False,
            "payments": False,
            "include_edge_cases": True,
        },
    },
    # Steps: health, project_types, create_project, generate,
    #   generate_components, update_components, generate_diagrams,
    #   approve_architecture, generate_pricing, staged_flow
    "steps": [
        "generate_pricing",
        # "generate_diagrams"
    ],
    # Optional override for update_components; when omitted, uses prior output.
    "components_update": None,
    "write_output": True,
    "output_file": "local_output.json",
}


def _ensure_debug_user(db: Session, profile: dict[str, str]) -> User:
    user = db.query(User).filter(User.google_sub == profile["google_sub"]).one_or_none()
    if user is None:
        user = User(
            google_sub=profile["google_sub"],
            email=profile["email"],
            name=profile["name"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created debug user id=%s", user.id)
    else:
        logger.info("Using existing debug user id=%s", user.id)
    return user


def _build_controller(db: Session, *, use_mock_ai: bool) -> ProjectController:
    if use_mock_ai:
        from tests.fixtures import VALID_AI_RESPONSE_JSON

        class LocalMockAIClient(BaseAIClient):
            def generate(self, prompt: str) -> str:
                return VALID_AI_RESPONSE_JSON

        ai_client = LocalMockAIClient()
        logger.info("Local debug mode: mock AI response (no remote OpenAI).")
    else:
        ai_client = AIClientFactory.create()
        logger.info("Local debug mode: real OpenAI client (in-process, not via HTTP).")
    return ProjectController(
        ProjectService(db),
        GenerationService(db, ai_client=ai_client),
        CatalogService(db),
    )


def _to_body(detail: ProjectDetail) -> dict[str, Any]:
    return detail.model_dump(mode="json")


def _print_result(label: str, detail: ProjectDetail | list[ProjectDetail] | dict) -> dict[str, Any]:
    print(f"\n=== {label} (local in-process) ===")
    if isinstance(detail, ProjectDetail):
        body = _to_body(detail)
    elif isinstance(detail, list):
        body = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in detail]
    else:
        body = detail
    print(json.dumps(body, indent=2, default=str))
    return body if isinstance(body, dict) else {}


def _components_payload(components: list[dict[str, Any]]) -> ComponentsUpdate:
    return ComponentsUpdate.model_validate(
        {
            "components": [
                {
                    "key": component["key"],
                    "name": component["name"],
                    "type": component["type"],
                    "reason": component["reason"],
                    "optional": component["optional"],
                    "cloud_mappings": component.get("cloud_mappings")
                    or {"aws": None, "gcp": None, "azure": None},
                }
                for component in components
            ]
        }
    )


def _run_step(
    controller: ProjectController,
    step: str,
    *,
    user: User,
    project_id: str | None,
    last_body: dict[str, Any] | None,
    event: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    if step == "health":
        _print_result("health", HealthController().check())
        return project_id, last_body

    if step == "project_types":
        _print_result("project_types", controller.list_project_types())
        return project_id, last_body

    if step == "create_project":
        payload = ProjectCreate.model_validate(event["project_create"])
        detail = controller.create_project(payload, user)
        body = _print_result("create_project", detail)
        return detail.id, body

    if project_id is None:
        raise RuntimeError(f"step={step!r} requires project_id (run create_project first)")

    if step == "generate":
        detail = controller.generate_project(project_id, user)
        return project_id, _print_result("generate", detail)

    if step == "generate_components":
        detail = controller.generate_components(project_id, user)
        return project_id, _print_result("generate_components", detail)

    if step == "update_components":
        payload_data = event.get("components_update")
        if payload_data is None:
            if not last_body or not last_body.get("components"):
                raise RuntimeError("update_components needs components from prior step")
            payload = _components_payload(last_body["components"])
        else:
            payload = ComponentsUpdate.model_validate(payload_data)
        detail = controller.update_components(project_id, payload, user)
        return project_id, _print_result("update_components", detail)

    if step == "generate_diagrams":
        detail = controller.generate_diagrams(project_id, user)
        return project_id, _print_result("generate_diagrams", detail)

    if step == "approve_architecture":
        detail = controller.approve_architecture(project_id, user)
        return project_id, _print_result("approve_architecture", detail)

    if step == "generate_pricing":
        detail = controller.generate_pricing(project_id, user)
        return project_id, _print_result("generate_pricing", detail)

    if step == "staged_flow":
        for staged_step in (
            "generate_components",
            "update_components",
            "generate_diagrams",
            "approve_architecture",
            "generate_pricing",
        ):
            project_id, last_body = _run_step(
                controller,
                staged_step,
                user=user,
                project_id=project_id,
                last_body=last_body,
                event=event,
            )
        return project_id, last_body

    raise ValueError(f"Unknown step: {step!r}")


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        debug_user = _ensure_debug_user(db, EVENT["user"])
        controller = _build_controller(db, use_mock_ai=bool(EVENT.get("use_mock_ai", False)))

        project_id = EVENT.get("project_id")
        last_body: dict[str, Any] | None = None

        for step in EVENT["steps"]:
            logger.info("Running step locally: %s", step)
            project_id, last_body = _run_step(
                controller,
                step,
                user=debug_user,
                project_id=project_id,
                last_body=last_body,
                event=EVENT,
            )

        if EVENT.get("write_output") and last_body:
            output_path = _BACKEND_DIR / EVENT.get("output_file", "local_output.json")
            output_path.write_text(
                json.dumps(last_body, indent=2, default=str),
                encoding="utf-8",
            )
            logger.info("Wrote output to %s", output_path)
    finally:
        db.close()


if __name__ == "__main__":
    main()
