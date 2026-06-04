"""Orchestrates AI architecture generation and persists the result."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..rules.cost_estimator import estimate_costs
from .ai_client import AIClientError, generate_architecture
from .ai_validator import AIValidationError, validate_ai_response
from .component_mapper import feature_flags_from_components, map_ai_payload
from .prompt_builder import build_generation_prompt

logger = logging.getLogger(__name__)


def _log_step(
    step: str,
    *,
    project_id: str,
    request_id: str,
    status: str,
    reason: str | None = None,
) -> None:
    message = (
        f"generation step={step} status={status} "
        f"project_id={project_id} request_id={request_id}"
    )
    if reason:
        message = f"{message} reason={reason}"
    if status == "failed":
        logger.error(message)
    elif status == "started":
        logger.info(message)
    else:
        logger.info(message)


class ArchitectureGenerationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _clear_previous(project: models.Project) -> None:
    project.components.clear()
    project.cost_estimates.clear()
    project.risks.clear()
    project.recommendations.clear()


def _persist_document(
    project: models.Project,
    *,
    components,
    costs,
    risks,
    recommendations,
    main_flow,
    next_steps,
    architecture_summary,
    architecture_diagrams,
) -> None:
    _clear_previous(project)

    for comp in components:
        component = models.ArchitectureComponent(
            key=comp.key,
            name=comp.name,
            component_type=comp.component_type,
            reason=comp.reason,
            category=comp.category,
            optional=comp.optional,
            order=comp.order,
        )
        component.cloud_mapping = models.CloudMapping(
            aws=comp.cloud.get("aws", []),
            gcp=comp.cloud.get("gcp", []),
            azure=comp.cloud.get("azure", []),
        )
        project.components.append(component)

    for cost in costs:
        project.cost_estimates.append(
            models.CostEstimate(
                provider=cost.provider,
                monthly_low=cost.monthly_low,
                monthly_high=cost.monthly_high,
                currency=cost.currency,
                notes=cost.notes,
            )
        )

    for risk in risks:
        project.risks.append(
            models.Risk(title=risk.title, description=risk.description, severity=risk.severity)
        )

    for rec in recommendations:
        project.recommendations.append(models.Recommendation(text=rec))

    project.main_flow = main_flow
    project.next_steps = next_steps
    project.architecture_summary = architecture_summary
    project.architecture_diagrams = architecture_diagrams
    project.architecture_diagram = None
    project.generated_at = datetime.now(timezone.utc)


def _mark_failed(
    db: Session,
    generation_request: models.ArchitectureGenerationRequest,
    *,
    step: str,
    project_id: str,
    reason: str,
) -> None:
    _log_step(
        step,
        project_id=project_id,
        request_id=generation_request.id,
        status="failed",
        reason=reason,
    )
    generation_request.status = "failed"
    generation_request.end_time = datetime.now(timezone.utc)
    generation_request.updated_at = generation_request.end_time
    db.commit()


def generate_for_project(db: Session, project: models.Project) -> models.Project:
    now = datetime.now(timezone.utc)
    step = "create_request"
    _log_step(step, project_id=project.id, request_id="pending", status="started")

    generation_request = models.ArchitectureGenerationRequest(
        status="pending",
        project_id=project.id,
        start_time=now,
    )
    db.add(generation_request)
    db.flush()

    request_id = generation_request.id
    _log_step(step, project_id=project.id, request_id=request_id, status="completed")

    try:
        step = "build_prompt"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        prompt = build_generation_prompt(project)
        _log_step(step, project_id=project.id, request_id=request_id, status="completed")

        step = "save_prompt"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        prompts_dir = Path(settings.ai_prompts_dir)
        outputs_dir = Path(settings.ai_outputs_dir)
        prompts_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        input_path = prompts_dir / f"{generation_request.id}_input.txt"
        output_path = outputs_dir / f"{generation_request.id}_output.json"
        input_path.write_text(prompt, encoding="utf-8")
        generation_request.input_os_path = str(input_path.resolve())
        generation_request.updated_at = now
        db.flush()
        _log_step(
            step,
            project_id=project.id,
            request_id=request_id,
            status="completed",
            reason=f"path={generation_request.input_os_path}",
        )

        step = "call_ai"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        raw_response = generate_architecture(prompt)
        _log_step(
            step,
            project_id=project.id,
            request_id=request_id,
            status="completed",
            reason=f"response_chars={len(raw_response)}",
        )

        step = "validate_response"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        validated = validate_ai_response(raw_response)
        _log_step(step, project_id=project.id, request_id=request_id, status="completed")

        step = "save_output"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        output_path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        generation_request.output_os_path = str(output_path.resolve())
        _log_step(
            step,
            project_id=project.id,
            request_id=request_id,
            status="completed",
            reason=f"path={generation_request.output_os_path}",
        )

        step = "map_payload"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        components, risks, recommendations, next_steps, summary, main_flow = map_ai_payload(
            validated
        )
        _log_step(
            step,
            project_id=project.id,
            request_id=request_id,
            status="completed",
            reason=f"components={len(components)} risks={len(risks)}",
        )

        step = "estimate_costs"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        flags = feature_flags_from_components(components)
        costs = estimate_costs(
            expected_users=project.expected_users,
            stage=project.stage,
            file_upload=flags["file_upload"],
            ai=flags["ai"],
            background_processing=flags["background_processing"],
        )
        _log_step(
            step,
            project_id=project.id,
            request_id=request_id,
            status="completed",
            reason=f"estimates={len(costs)}",
        )

        step = "persist_document"
        _log_step(step, project_id=project.id, request_id=request_id, status="started")
        _persist_document(
            project,
            components=components,
            costs=costs,
            risks=risks,
            recommendations=recommendations,
            main_flow=main_flow,
            next_steps=next_steps,
            architecture_summary=summary,
            architecture_diagrams=validated["diagrams"],
        )
        _log_step(step, project_id=project.id, request_id=request_id, status="completed")

        generation_request.status = "completed"
        generation_request.end_time = datetime.now(timezone.utc)
        generation_request.updated_at = generation_request.end_time
        _log_step(
            "complete",
            project_id=project.id,
            request_id=request_id,
            status="completed",
        )

    except (AIClientError, AIValidationError) as exc:
        reason = str(exc)
        _mark_failed(db, generation_request, step=step, project_id=project.id, reason=reason)
        raise ArchitectureGenerationError(reason) from exc

    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        _mark_failed(db, generation_request, step=step, project_id=project.id, reason=reason)
        raise ArchitectureGenerationError(f"Architecture generation failed: {exc}") from exc

    db.commit()
    db.refresh(project)
    return project
