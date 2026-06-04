"""Orchestrates AI architecture generation and persists the result."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.config.settings import settings
from app.core.exceptions import AIClientError, AIValidationError, ArchitectureGenerationError
from app.core.logging import GenerationLogger
from app.models import ArchitectureGenerationRequest, Project
from app.repositories.generation_request_repository import GenerationRequestRepository
from app.repositories.project_repository import ProjectRepository
from app.services.component_mapper_service import ComponentMapperService
from app.services.cost_estimator_service import CostEstimatorService
from app.services.prompt_builder_service import PromptBuilderService
from app.validators.ai_response_validator import AIResponseValidator


class GenerationService:
    """Runs the full architecture generation pipeline for a project."""

    def __init__(
        self,
        db: Session,
        *,
        ai_client: BaseAIClient | None = None,
        prompt_builder: PromptBuilderService | None = None,
        validator: AIResponseValidator | None = None,
        mapper: ComponentMapperService | None = None,
        cost_estimator: CostEstimatorService | None = None,
        project_repo: ProjectRepository | None = None,
        request_repo: GenerationRequestRepository | None = None,
        logger: GenerationLogger | None = None,
    ) -> None:
        self._db = db
        self._ai_client = ai_client or AIClientFactory.create()
        self._prompt_builder = prompt_builder or PromptBuilderService()
        self._validator = validator or AIResponseValidator()
        self._mapper = mapper or ComponentMapperService()
        self._cost_estimator = cost_estimator or CostEstimatorService()
        self._project_repo = project_repo or ProjectRepository(db)
        self._request_repo = request_repo or GenerationRequestRepository(db)
        self._logger = logger or GenerationLogger()
        self._prompts_dir = Path(settings.ai_prompts_dir)
        self._outputs_dir = Path(settings.ai_outputs_dir)

    def generate(self, project: Project) -> Project:
        request = self._create_request(project)
        request_id = request.id
        current_step = "create_request"

        try:
            current_step = "build_prompt"
            prompt = self._build_prompt(project, request_id)

            current_step = "save_prompt"
            self._save_prompt(request, prompt, project.id, request_id)

            current_step = "call_ai"
            raw_response = self._call_ai(prompt, project.id, request_id)

            current_step = "validate_response"
            validated = self._validate_response(raw_response, project.id, request_id)

            current_step = "save_output"
            self._save_output(request, validated, project.id, request_id)

            current_step = "map_payload"
            mapped = self._map_payload(validated, project.id, request_id)

            current_step = "estimate_costs"
            costs = self._estimate_costs(project, mapped["components"], project.id, request_id)

            current_step = "persist_document"
            self._persist_document(project, mapped, costs, validated["diagrams"], request_id)

            self._complete_request(request, project.id, request_id)
        except (AIClientError, AIValidationError) as exc:
            self._handle_failure(request, current_step, project.id, str(exc))
            raise ArchitectureGenerationError(str(exc)) from exc
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            self._handle_failure(request, current_step, project.id, reason)
            raise ArchitectureGenerationError(f"Architecture generation failed: {exc}") from exc

        self._project_repo.commit()
        self._project_repo.refresh(project)
        return project

    def _create_request(self, project: Project) -> ArchitectureGenerationRequest:
        self._logger.log_step(
            "create_request", project_id=project.id, request_id="pending", status="started"
        )
        request = self._request_repo.create_pending(project)
        self._request_repo.flush()
        self._logger.log_step(
            "create_request",
            project_id=project.id,
            request_id=request.id,
            status="completed",
        )
        return request

    def _build_prompt(self, project: Project, request_id: str) -> str:
        self._logger.log_step(
            "build_prompt", project_id=project.id, request_id=request_id, status="started"
        )
        prompt = self._prompt_builder.build(project)
        self._logger.log_step(
            "build_prompt", project_id=project.id, request_id=request_id, status="completed"
        )
        return prompt

    def _save_prompt(
        self,
        request: ArchitectureGenerationRequest,
        prompt: str,
        project_id: str,
        request_id: str,
    ) -> None:
        self._logger.log_step(
            "save_prompt", project_id=project_id, request_id=request_id, status="started"
        )
        self._ensure_artifact_dirs()
        input_path = self._prompts_dir / f"{request.id}_input.txt"
        input_path.write_text(prompt, encoding="utf-8")
        self._request_repo.save_prompt_path(request, str(input_path.resolve()))
        self._request_repo.flush()
        self._logger.log_step(
            "save_prompt",
            project_id=project_id,
            request_id=request_id,
            status="completed",
            reason=f"path={request.input_os_path}",
        )

    def _call_ai(self, prompt: str, project_id: str, request_id: str) -> str:
        self._logger.log_step(
            "call_ai", project_id=project_id, request_id=request_id, status="started"
        )
        raw_response = self._ai_client.generate(prompt)
        self._logger.log_step(
            "call_ai",
            project_id=project_id,
            request_id=request_id,
            status="completed",
            reason=f"response_chars={len(raw_response)}",
        )
        return raw_response

    def _validate_response(self, raw: str, project_id: str, request_id: str) -> dict:
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="started"
        )
        validated = self._validator.validate(raw)
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="completed"
        )
        return validated

    def _save_output(
        self,
        request: ArchitectureGenerationRequest,
        validated: dict,
        project_id: str,
        request_id: str,
    ) -> None:
        self._logger.log_step(
            "save_output", project_id=project_id, request_id=request_id, status="started"
        )
        output_path = self._outputs_dir / f"{request.id}_output.json"
        output_path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        self._request_repo.save_output_path(request, str(output_path.resolve()))
        self._logger.log_step(
            "save_output",
            project_id=project_id,
            request_id=request_id,
            status="completed",
            reason=f"path={request.output_os_path}",
        )

    def _map_payload(self, validated: dict, project_id: str, request_id: str) -> dict:
        self._logger.log_step(
            "map_payload", project_id=project_id, request_id=request_id, status="started"
        )
        components, risks, recommendations, next_steps, summary, main_flow = (
            self._mapper.map_payload(validated)
        )
        self._logger.log_step(
            "map_payload",
            project_id=project_id,
            request_id=request_id,
            status="completed",
            reason=f"components={len(components)} risks={len(risks)}",
        )
        return {
            "components": components,
            "risks": risks,
            "recommendations": recommendations,
            "next_steps": next_steps,
            "summary": summary,
            "main_flow": main_flow,
        }

    def _estimate_costs(self, project: Project, components, project_id: str, request_id: str):
        self._logger.log_step(
            "estimate_costs", project_id=project_id, request_id=request_id, status="started"
        )
        flags = self._mapper.feature_flags_from_components(components)
        costs = self._cost_estimator.estimate(
            expected_users=project.expected_users,
            stage=project.stage,
            file_upload=flags["file_upload"],
            ai=flags["ai"],
            background_processing=flags["background_processing"],
        )
        self._logger.log_step(
            "estimate_costs",
            project_id=project_id,
            request_id=request_id,
            status="completed",
            reason=f"estimates={len(costs)}",
        )
        return costs

    def _persist_document(
        self,
        project: Project,
        mapped: dict,
        costs,
        diagrams: dict,
        request_id: str,
    ) -> None:
        self._logger.log_step(
            "persist_document",
            project_id=project.id,
            request_id=request_id,
            status="started",
        )
        self._project_repo.persist_architecture(
            project,
            components=mapped["components"],
            costs=costs,
            risks=mapped["risks"],
            recommendations=mapped["recommendations"],
            main_flow=mapped["main_flow"],
            next_steps=mapped["next_steps"],
            architecture_summary=mapped["summary"],
            architecture_diagrams=diagrams,
        )
        self._logger.log_step(
            "persist_document",
            project_id=project.id,
            request_id=request_id,
            status="completed",
        )

    def _complete_request(
        self,
        request: ArchitectureGenerationRequest,
        project_id: str,
        request_id: str,
    ) -> None:
        self._request_repo.mark_completed(request)
        self._logger.log_step(
            "complete", project_id=project_id, request_id=request_id, status="completed"
        )

    def _handle_failure(
        self,
        request: ArchitectureGenerationRequest,
        step: str,
        project_id: str,
        reason: str,
    ) -> None:
        self._logger.log_step(
            step, project_id=project_id, request_id=request.id, status="failed", reason=reason
        )
        self._request_repo.mark_failed(request)
        self._request_repo.commit()

    def _ensure_artifact_dirs(self) -> None:
        self._prompts_dir.mkdir(parents=True, exist_ok=True)
        self._outputs_dir.mkdir(parents=True, exist_ok=True)


def generate_for_project(db: Session, project: Project) -> Project:
    """Convenience wrapper used by tests and legacy callers."""
    return GenerationService(db).generate(project)
