"""Orchestrates AI architecture generation and persists the result."""

from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.core.exceptions import AIClientError, AIValidationError, ArchitectureGenerationError
from app.core.logging import GenerationLogger
from app.models import ArchitectureGenerationRequest, Project
from app.repositories.generation_request_repository import GenerationRequestRepository
from app.repositories.project_repository import ProjectRepository
from app.services.component_mapper_service import ComponentMapperService
from app.services.cost_estimator_service import CostEstimatorService
from app.services.generation_storage_service import GenerationStorageService
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
        generation_storage: GenerationStorageService | None = None,
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
        self._generation_storage = generation_storage or GenerationStorageService()
        self._logger = logger or GenerationLogger()

    def generate(self, project: Project) -> Project:
        request = self._create_request(project)
        request_id = request.id
        model_name = self._generation_storage.resolve_model_name()
        current_step = "create_request"

        raw_response: str | None = None
        parsed_response: dict | None = None
        validation_result: dict | None = None
        errors: list[str] = []
        duration_seconds: float | None = None
        request_saved = False

        try:
            current_step = "build_prompt"
            prompt = self._build_prompt(project, request_id)

            current_step = "save_generation_request"
            request_payload = self._generation_storage.build_request_payload(
                project,
                generation_id=request_id,
                prompt=prompt,
                model_name=model_name,
            )
            request_path = self._generation_storage.save_request(
                project.id, request_id, request_payload
            )
            self._request_repo.save_prompt_path(request, request_path)
            self._request_repo.flush()
            request_saved = True

            current_step = "call_ai"
            ai_started = time.monotonic()
            try:
                raw_response = self._call_ai(prompt, project.id, request_id)
            except AIClientError as exc:
                duration_seconds = time.monotonic() - ai_started
                errors.append(str(exc))
                self._save_generation_response(
                    request,
                    project.id,
                    request_id,
                    model_name,
                    raw_response=raw_response,
                    parsed_response=parsed_response,
                    validation_result=validation_result,
                    errors=errors,
                    duration_seconds=duration_seconds,
                )
                raise
            duration_seconds = time.monotonic() - ai_started

            current_step = "validate_response"
            try:
                validated = self._validate_response(raw_response, project.id, request_id)
                parsed_response = validated
                validation_result = {"valid": True}
            except AIValidationError as exc:
                errors.append(str(exc))
                self._save_generation_response(
                    request,
                    project.id,
                    request_id,
                    model_name,
                    raw_response=raw_response,
                    parsed_response=parsed_response,
                    validation_result=validation_result,
                    errors=errors,
                    duration_seconds=duration_seconds,
                )
                raise

            self._save_generation_response(
                request,
                project.id,
                request_id,
                model_name,
                raw_response=raw_response,
                parsed_response=parsed_response,
                validation_result=validation_result,
                errors=errors or None,
                duration_seconds=duration_seconds,
            )

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
            if request_saved:
                errors.append(reason)
                self._save_generation_response(
                    request,
                    project.id,
                    request_id,
                    model_name,
                    raw_response=raw_response,
                    parsed_response=parsed_response,
                    validation_result=validation_result,
                    errors=errors,
                    duration_seconds=duration_seconds,
                )
            self._handle_failure(request, current_step, project.id, reason)
            raise ArchitectureGenerationError(f"Architecture generation failed: {exc}") from exc

        self._project_repo.commit()
        self._project_repo.refresh(project)
        return project

    def _save_generation_response(
        self,
        request: ArchitectureGenerationRequest,
        project_id: str,
        generation_id: str,
        model_name: str,
        *,
        raw_response: str | None,
        parsed_response: dict | None,
        validation_result: dict | None,
        errors: list[str] | None,
        duration_seconds: float | None,
    ) -> None:
        payload = self._generation_storage.build_response_payload(
            generation_id=generation_id,
            project_id=project_id,
            model_name=model_name,
            raw_ai_response=raw_response,
            parsed_response=parsed_response,
            validation_result=validation_result,
            errors=errors,
            duration_seconds=duration_seconds,
        )
        response_path = self._generation_storage.save_response(
            project_id, generation_id, payload
        )
        self._request_repo.save_output_path(request, response_path)
        self._request_repo.flush()

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


def generate_for_project(db: Session, project: Project) -> Project:
    """Convenience wrapper used by tests and legacy callers."""
    return GenerationService(db).generate(project)
