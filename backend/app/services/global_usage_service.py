"""Application-level orchestration for Step 3 (global usage model).

Ties together the pipeline:

    load project -> load selection -> resolve LLM + static parameter names ->
    resolve static values from project -> LLM service for behavioral params ->
    persist combined model -> return API response.
"""

from __future__ import annotations

import logging
from typing import Any

from google.cloud import firestore

from app.config.params import (
    ERR_NO_COMPONENT_SELECTION,
    ERR_NO_GLOBAL_USAGE_MODEL,
    ERR_NO_USAGE_PARAMETERS,
    ERR_PROJECT_FORBIDDEN,
    ERR_PROJECT_NOT_FOUND,
    GLOBAL_USAGE_MODEL_PROMPT_VERSION,
)
from app.config.settings import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ServiceUnavailableError
from app.clients.storage_client import StorageClientFactory
from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import UserOut
from app.schemas.global_usage_model import (
    GlobalUsageModelEstimateResult,
    GlobalUsageModelPayload,
    GlobalUsageModelResponse,
)
from app.services.global_usage_model_service import GlobalUsageModelService
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_parameter_resolver import UsageParameterResolver
from app.services.usage_model_debug_csv_builder import build_usage_model_debug_csv

logger = logging.getLogger(__name__)


class GlobalUsageService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        usage_parameter_resolver: UsageParameterResolver,
        static_value_resolver: StaticUsageValueResolver,
        usage_model_service: GlobalUsageModelService,
    ) -> None:
        self._projects = project_repository
        self._parameter_resolver = usage_parameter_resolver
        self._static_values = static_value_resolver
        self._usage_model = usage_model_service

    def generate(self, project_id: str, user: UserOut) -> GlobalUsageModelResponse:
        project = self._load_owned_project(project_id, user)
        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)

        selected = list(selection.get("selected", []))
        resolved_parameters = self._parameter_resolver.resolve_for_selected_components(
            selected
        )
        if not resolved_parameters.llm and not resolved_parameters.static:
            raise ServiceUnavailableError(ERR_NO_USAGE_PARAMETERS)

        normalized_input = self._normalize_input(project)

        static_values = self._static_values.resolve(
            resolved_parameters.static,
            expected_users=normalized_input["expected_users"],
            stage=normalized_input["stage"],
            requirements=normalized_input["requirements"],
        )

        llm_estimate: GlobalUsageModelEstimateResult | None = None
        if resolved_parameters.llm:
            llm_estimate = self._usage_model.estimate(
                selected_components=selected,
                usage_parameters=resolved_parameters.llm,
                static_usage_values=static_values,
                **normalized_input,
            )

        payload = GlobalUsageModelPayload(
            llm=llm_estimate.result.usage if llm_estimate else {},
            static=static_values,
        )

        model_id = self._persist(
            project_id,
            selection_id=selection["id"],
            payload=payload,
            llm_estimate=llm_estimate,
            llm_parameters=resolved_parameters.llm,
            static_parameters=resolved_parameters.static,
            usage_used_by=resolved_parameters.used_by,
            normalized_input=normalized_input,
            selected_components=selected,
        )
        return GlobalUsageModelResponse.from_payload(
            model_id=model_id,
            selection_id=selection["id"],
            llm_parameters=resolved_parameters.llm,
            static_parameters=resolved_parameters.static,
            payload=payload,
        )

    def get_usage_model(self, project_id: str, user: UserOut) -> GlobalUsageModelResponse:
        self._load_owned_project(project_id, user)
        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)

        usage_model = self._projects.get_latest_global_usage_model(project_id)
        if not self._is_usage_model_current(usage_model, selection["id"]):
            raise NotFoundError(ERR_NO_GLOBAL_USAGE_MODEL)
        return GlobalUsageModelResponse.from_stored_document(usage_model)

    def _load_owned_project(self, project_id: str, user: UserOut) -> dict[str, Any]:
        project = self._projects.find_by_id(project_id)
        if project is None:
            raise NotFoundError(ERR_PROJECT_NOT_FOUND)
        if project.get("user_id") != user.id:
            raise ForbiddenError(ERR_PROJECT_FORBIDDEN)
        return project

    @staticmethod
    def _normalize_input(project: dict[str, Any]) -> dict[str, Any]:
        return {
            "application_description": project.get("description", ""),
            "platform": project.get("platform", "web"),
            "stage": project.get("stage", ""),
            "expected_users": int(project.get("expected_users", 0) or 0),
            "requirements": project.get("requirements", {}) or {},
        }

    def _persist(
        self,
        project_id: str,
        *,
        selection_id: str,
        payload: GlobalUsageModelPayload,
        llm_estimate: GlobalUsageModelEstimateResult | None,
        llm_parameters: list[str],
        static_parameters: list[str],
        usage_used_by: dict[str, list[str]],
        normalized_input: dict[str, Any],
        selected_components: list[dict[str, Any]],
    ) -> str:
        model_name = "static" if settings.use_static_ai_response else settings.openai_model
        document = {
            "selection_id": selection_id,
            "stale": False,
            "llm_parameters": llm_parameters,
            "static_parameters": static_parameters,
            "usage_model": {
                "llm": {
                    parameter: estimate.model_dump(mode="json")
                    for parameter, estimate in payload.llm.items()
                },
                "static": payload.static,
            },
            "prompt": llm_estimate.prompt if llm_estimate else None,
            "raw_response": llm_estimate.raw_response if llm_estimate else None,
            "model_output": (
                llm_estimate.result.model_dump(mode="json") if llm_estimate else None
            ),
            "created_at": firestore.SERVER_TIMESTAMP,
            "prompt_version": GLOBAL_USAGE_MODEL_PROMPT_VERSION,
            "model": model_name if llm_parameters else None,
            "input": {
                "application_description": normalized_input["application_description"],
                "platform": normalized_input["platform"],
                "stage": normalized_input["stage"],
                "expected_users": normalized_input["expected_users"],
                "requirements": normalized_input["requirements"],
                "selected_components": selected_components,
                "llm_parameters": llm_parameters,
                "static_parameters": static_parameters,
            },
        }
        model_id = self._projects.save_global_usage_model(project_id, document)
        logger.info(
            "saved global usage model project_id=%s model_id=%s llm=%d static=%d",
            project_id,
            model_id,
            len(llm_parameters),
            len(static_parameters),
        )

        # Best-effort debug artifact: never fail Step 3 if storage write fails.
        try:
            object_path = (
                f"projects/{project_id}/usage-models/{model_id}/usage_model_debug.csv"
            )
            update_fn = getattr(
                self._projects, "update_global_usage_model_debug_csv_path", None
            )
            if callable(update_fn):
                try:
                    update_fn(project_id, model_id, object_path)
                except Exception:
                    logger.exception(
                        "usage_model_debug.csv Firestore path update failed (project_id=%s model_id=%s).",
                        project_id,
                        model_id,
                    )

            debug_bucket = "archsari-debug-artifacts-prod"

            storage = StorageClientFactory.create(bucket_name=debug_bucket)

            debug_csv = build_usage_model_debug_csv(payload, used_by=usage_used_by)
            storage.write_csv(object_path, debug_csv)
        except Exception:
            logger.exception(
                "usage_model_debug.csv upload failed (project_id=%s model_id=%s).",
                project_id,
                model_id,
            )

        return model_id

    @staticmethod
    def _is_usage_model_current(
        usage_model: dict[str, Any] | None, selection_id: str
    ) -> bool:
        if usage_model is None or usage_model.get("stale"):
            return False
        return usage_model.get("selection_id") == selection_id
