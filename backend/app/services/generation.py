"""Orchestrates AI architecture generation and persists the result."""

from __future__ import annotations

import json
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


def generate_for_project(db: Session, project: models.Project) -> models.Project:
    now = datetime.now(timezone.utc)
    generation_request = models.ArchitectureGenerationRequest(
        status="pending",
        project_id=project.id,
        start_time=now,
    )
    db.add(generation_request)
    db.flush()

    prompt = build_generation_prompt(project)
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

    try:
        validated = validate_ai_response(generate_architecture(prompt))
        output_path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        generation_request.output_os_path = str(output_path.resolve())

        components, risks, recommendations, next_steps, summary, main_flow = map_ai_payload(
            validated
        )
        flags = feature_flags_from_components(components)
        costs = estimate_costs(
            expected_users=project.expected_users,
            stage=project.stage,
            file_upload=flags["file_upload"],
            ai=flags["ai"],
            background_processing=flags["background_processing"],
        )

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

        generation_request.status = "completed"
        generation_request.end_time = datetime.now(timezone.utc)
        generation_request.updated_at = generation_request.end_time

    except (AIClientError, AIValidationError) as exc:
        generation_request.status = "failed"
        generation_request.end_time = datetime.now(timezone.utc)
        generation_request.updated_at = generation_request.end_time
        db.commit()
        raise ArchitectureGenerationError(str(exc)) from exc

    except Exception as exc:
        generation_request.status = "failed"
        generation_request.end_time = datetime.now(timezone.utc)
        generation_request.updated_at = generation_request.end_time
        db.commit()
        raise ArchitectureGenerationError(f"Architecture generation failed: {exc}") from exc

    db.commit()
    db.refresh(project)
    return project
