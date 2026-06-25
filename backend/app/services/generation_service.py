"""Orchestrates staged AI architecture generation and persists results."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy.orm import Session

from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.config.params import (
    ERR_INVALID_WORKFLOW_STATUS,
    WORKFLOW_ALLOWED_FOR_GENERATE_COMPONENTS,
    WORKFLOW_ALLOWED_FOR_GENERATE_PRICING,
)
from app.core.exceptions import AIClientError, AIValidationError, ArchitectureGenerationError, BadRequestError
from app.core.logging import GenerationLogger
from app.models import ArchitectureGenerationRequest, Project
from app.repositories.generation_request_repository import GenerationRequestRepository
from app.repositories.project_repository import ProjectRepository
from app.services.architecture_guardrail_service import ArchitectureGuardrailService
from app.services.catalog_service import CatalogService
from app.services.cloud_defaults_service import CloudDefaultsService
from app.services.component_mapper_service import ComponentMapperService
from app.services.cost_estimator_service import CostEstimatorService
from app.services.diagram_rules_service import DiagramRulesService
from app.services.generation_storage_service import GenerationStorageService
from app.services.prompt_builder_service import PromptBuilderService
from app.validators.ai_response_validator import AIResponseValidator


@dataclass
class _GenerationRun:
    project: Project
    request: ArchitectureGenerationRequest
    model_name: str
    current_step: str = "create_request"
    raw_response: str | None = None
    parsed_response: dict | None = None
    validation_result: dict | None = None
    errors: list[str] = field(default_factory=list)
    duration_seconds: float | None = None
    request_saved: bool = False

    @property
    def request_id(self) -> str:
        return self.request.id

    @property
    def project_id(self) -> str:
        return self.project.id


class GenerationService:
    def __init__(
        self,
        db: Session,
        *,
        ai_client: BaseAIClient | None = None,
        catalog_service: CatalogService | None = None,
        cloud_defaults: CloudDefaultsService | None = None,
        prompt_builder: PromptBuilderService | None = None,
        validator: AIResponseValidator | None = None,
        guardrails: ArchitectureGuardrailService | None = None,
        diagram_rules: DiagramRulesService | None = None,
        mapper: ComponentMapperService | None = None,
        cost_estimator: CostEstimatorService | None = None,
        project_repo: ProjectRepository | None = None,
        request_repo: GenerationRequestRepository | None = None,
        generation_storage: GenerationStorageService | None = None,
        logger: GenerationLogger | None = None,
    ) -> None:
        self._db = db
        self._ai_client = ai_client or AIClientFactory.create()
        self._catalog = catalog_service or CatalogService(db)
        self._cloud_defaults = cloud_defaults or CloudDefaultsService(self._catalog._catalog_repo)
        self._prompt_builder = prompt_builder or PromptBuilderService(self._catalog)
        self._validator = validator or AIResponseValidator(self._cloud_defaults, self._catalog)
        self._guardrails = guardrails or ArchitectureGuardrailService()
        self._diagram_rules = diagram_rules or DiagramRulesService(
            supporting_infrastructure_types=self._catalog.supporting_infrastructure_types(),
            main_architecture_types=self._catalog.main_architecture_types(),
        )
        self._mapper = mapper or ComponentMapperService(self._catalog)
        self._cost_estimator = cost_estimator or CostEstimatorService()
        self._project_repo = project_repo or ProjectRepository(db)
        self._request_repo = request_repo or GenerationRequestRepository(db)
        self._generation_storage = generation_storage or GenerationStorageService()
        self._logger = logger or GenerationLogger()

    def generate(self, project: Project) -> Project:
        """Legacy full pipeline: components, diagrams, and pricing in one operation."""
        project = self.generate_components(project)
        self._project_repo.replace_components(
            project,
            self._components_to_update_payload(project.components),
        )
        self._project_repo.commit()
        self._project_repo.refresh(project)
        project = self.generate_diagrams(project)
        self._project_repo.approve_architecture(project)
        self._project_repo.commit()
        self._project_repo.refresh(project)
        return self.generate_pricing(project)

    def generate_components(self, project: Project) -> Project:
        self._ensure_status(project, WORKFLOW_ALLOWED_FOR_GENERATE_COMPONENTS)
        return self._run_stage(
            project,
            step_name="generate_components",
            build_prompt=lambda current: self._prompt_builder.build_components(current),
            validate=self._validate_components_response,
            persist=self._persist_components_output,
        )

    def generate_diagrams(self, project: Project) -> Project:
        # self._ensure_status(project, self._DIAGRAMS_ALLOWED_STATUSES)
        if not project.components:
            raise BadRequestError("Approved components are required before generating diagrams.")
        return self._run_stage(
            project,
            step_name="generate_diagrams",
            build_prompt=lambda current: self._prompt_builder.build_diagrams(
                current, list(current.components)
            ),
            validate=self._validate_diagrams_response,
            persist=self._persist_diagrams_output,
        )

    def generate_pricing(self, project: Project) -> Project:
        self._ensure_status(project, WORKFLOW_ALLOWED_FOR_GENERATE_PRICING)
        if not project.components:
            raise BadRequestError("Components are required before generating pricing.")
        if not project.architecture_diagrams:
            raise BadRequestError("Architecture diagrams are required before generating pricing.")

        run = self._start_generation(project)
        try:
            run.current_step = "estimate_costs"
            mapped_components = self._mapper.map_components_from_db(project.components)
            costs = self._estimate_costs(
                run.project,
                mapped_components,
                run.project_id,
                run.request_id,
            )
            run.current_step = "persist_pricing"
            self._project_repo.persist_pricing(run.project, costs)
            self._complete_request(run.request, run.project_id, run.request_id)
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            self._fail_generation(run, reason)
            raise ArchitectureGenerationError(f"Pricing generation failed: {exc}") from exc

        return self._finish_generation(project)

    def _run_stage(
        self,
        project: Project,
        *,
        step_name: str,
        build_prompt: Callable[[Project], str],
        validate: Callable[[str, Project, str, str], dict],
        persist: Callable[[_GenerationRun, dict], None],
    ) -> Project:
        run = self._start_generation(project)
        try:
            run.current_step = f"{step_name}_build_prompt"
            prompt = build_prompt(run.project)

            run.current_step = f"{step_name}_save_generation_request"
            self._persist_request_artifact(run, prompt)
            self._release_db_lock_for_ai(run)

            run.current_step = f"{step_name}_call_ai"
            self._call_ai_step(run, prompt)

            run.current_step = f"{step_name}_validate_response"
            validated = validate(
                run.raw_response or "",
                run.project,
                run.project_id,
                run.request_id,
            )
            run.parsed_response = validated
            run.validation_result = {"valid": True}

            self._record_successful_response(run)
            persist(run, validated)
            self._complete_request(run.request, run.project_id, run.request_id)
        except (AIClientError, AIValidationError) as exc:
            self._fail_generation(run, str(exc))
            raise ArchitectureGenerationError(str(exc)) from exc
        except BadRequestError:
            self._fail_generation(run, ERR_INVALID_WORKFLOW_STATUS)
            raise
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            self._record_unexpected_error(run, reason)
            self._fail_generation(run, reason)
            raise ArchitectureGenerationError(f"Architecture generation failed: {exc}") from exc

        return self._finish_generation(project)

    def _ensure_status(self, project: Project, allowed: set[str]) -> None:
        if project.workflow_status not in allowed:
            raise BadRequestError(ERR_INVALID_WORKFLOW_STATUS)

    def _validate_components_response(
        self,
        raw: str,
        project: Project,
        project_id: str,
        request_id: str,
    ) -> dict:
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="started"
        )
        validated = self._validator.validate_components(raw)
        validated = self._guardrails.apply(validated, project)
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="completed"
        )
        return validated

    def _validate_diagrams_response(
        self,
        raw: str,
        project: Project,
        project_id: str,
        request_id: str,
    ) -> dict:
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="started"
        )
        validated = self._validator.validate_diagrams(raw)
        validated = self._diagram_rules.apply(validated)
        self._logger.log_step(
            "validate_response", project_id=project_id, request_id=request_id, status="completed"
        )
        return validated

    def _persist_components_output(self, run: _GenerationRun, validated: dict) -> None:
        run.current_step = "map_payload"
        components, _, _ = self._mapper.map_payload(
            {"components": validated["components"], "architecture": {"summary": "", "flow": []}}
        )
        run.current_step = "persist_components"
        self._project_repo.persist_components(run.project, components)

    def _persist_diagrams_output(self, run: _GenerationRun, validated: dict) -> None:
        run.current_step = "map_payload"
        _, summary, main_flow = self._mapper.map_payload(
            {"components": [], "architecture": validated["architecture"]}
        )
        run.current_step = "persist_diagrams"
        self._project_repo.persist_diagrams(
            run.project,
            main_flow=main_flow,
            architecture_summary=summary,
            architecture_diagrams=validated["diagrams"],
        )

    @staticmethod
    def _components_to_update_payload(components):
        from app.schemas.project import CloudMappingIn, ComponentUpdateIn

        payload: list[ComponentUpdateIn] = []
        for component in components:
            cloud = component.cloud_mapping
            payload.append(
                ComponentUpdateIn(
                    key=component.key,
                    name=component.name,
                    type=component.component_type,
                    reason=component.reason,
                    optional=component.optional,
                    source=component.source or "ai_generated",
                    cloud_mapping=CloudMappingIn(
                        aws=cloud.aws if cloud else [],
                        gcp=cloud.gcp if cloud else [],
                        azure=cloud.azure if cloud else [],
                    ),
                    implementation_options=component.implementation_options,
                )
            )
        return payload

    def _start_generation(self, project: Project) -> _GenerationRun:
        request = self._create_request(project)
        return _GenerationRun(
            project=project,
            request=request,
            model_name=self._generation_storage.resolve_model_name(),
        )

    def _release_db_lock_for_ai(self, run: _GenerationRun) -> None:
        self._request_repo.commit()
        self._request_repo.refresh(run.request)
        self._project_repo.refresh(run.project)

    def _persist_request_artifact(self, run: _GenerationRun, prompt: str) -> None:
        request_payload = self._generation_storage.build_request_payload(
            run.project,
            generation_id=run.request_id,
            prompt=prompt,
            model_name=run.model_name,
        )
        request_path = self._generation_storage.save_request(run.request_id, request_payload)
        self._request_repo.save_prompt_path(run.request, request_path)
        self._request_repo.flush()
        run.request_saved = True

    def _call_ai_step(self, run: _GenerationRun, prompt: str) -> None:
        ai_started = time.monotonic()
        try:
            run.raw_response = self._call_ai(prompt, run.project_id, run.request_id)
        except AIClientError as exc:
            run.duration_seconds = time.monotonic() - ai_started
            run.errors.append(str(exc))
            self._save_run_response(run)
            raise
        run.duration_seconds = time.monotonic() - ai_started

    def _record_successful_response(self, run: _GenerationRun) -> None:
        self._save_run_response(run, errors=run.errors or None)

    def _record_unexpected_error(self, run: _GenerationRun, reason: str) -> None:
        if not run.request_saved:
            return
        run.errors.append(reason)
        self._save_run_response(run)

    def _save_run_response(
        self,
        run: _GenerationRun,
        *,
        errors: list[str] | None = None,
    ) -> None:
        self._save_generation_response(
            run.request,
            run.project_id,
            run.request_id,
            run.model_name,
            raw_response=run.raw_response,
            parsed_response=run.parsed_response,
            validation_result=run.validation_result,
            errors=errors if errors is not None else run.errors,
            duration_seconds=run.duration_seconds,
        )

    def _fail_generation(self, run: _GenerationRun, reason: str) -> None:
        self._handle_failure(run.request, run.current_step, run.project_id, reason)

    def _finish_generation(self, project: Project) -> Project:
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
        response_path = self._generation_storage.save_response(generation_id, payload)
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
