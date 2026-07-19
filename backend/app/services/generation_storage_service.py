"""Persists AI generation request/response JSON to object storage."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.clients.storage_client import StorageClient, StorageClientFactory
from app.config.params import (
    AI_RESPONSE_FORMAT,
    AI_SYSTEM_PROMPT,
    AI_TEMPERATURE,
    GENERATION_ARTIFACT_BUCKET,
    GENERATION_REQUEST_FILENAME,
    GENERATION_RESPONSE_FILENAME,
    GENERATION_STORAGE_PREFIX,
    GENERATION_TYPE_ARCHITECTURE,
    REQUIREMENT_KEYS,
)
from app.config.settings import settings
from app.models import Project

logger = logging.getLogger(__name__)


class GenerationStorageService:
    def __init__(self, storage: StorageClient | None = None) -> None:
        # Lazily bind to GCS so constructing the service (e.g. during dependency
        # injection or in tests) never requires GCS credentials. The client is
        # only created on the first write, which happens in the background task.
        self._storage = storage

    def build_request_payload(
        self,
        project: Project,
        *,
        generation_id: str,
        prompt: str,
        model_name: str,
    ) -> dict[str, Any]:
        return self._request_payload(
            generation_id=generation_id,
            project_id=project.id,
            user_id=project.user_id,
            project_types=project.project_types,
            original_user_input=self._original_user_input(project),
            prompt=prompt,
            model_name=model_name,
        )

    def build_selection_request_payload(
        self,
        *,
        generation_id: str,
        project_id: str,
        user_id: str | None,
        project_types: list[str] | None,
        original_user_input: dict[str, Any],
        prompt: str,
        model_name: str,
    ) -> dict[str, Any]:
        """Build the request artifact for the Step-2 component-selection flow.

        Unlike ``build_request_payload`` this accepts plain values (the live flow
        works with Firestore dicts rather than the ORM ``Project`` model).
        """

        return self._request_payload(
            generation_id=generation_id,
            project_id=project_id,
            user_id=user_id,
            project_types=project_types,
            original_user_input=original_user_input,
            prompt=prompt,
            model_name=model_name,
        )

    def _request_payload(
        self,
        *,
        generation_id: str,
        project_id: str,
        user_id: str | None,
        project_types: list[str] | None,
        original_user_input: dict[str, Any],
        prompt: str,
        model_name: str,
    ) -> dict[str, Any]:
        return {
            "generation_id": generation_id,
            "request_id": generation_id,
            "project_id": project_id,
            "user_id": user_id,
            "project_type": list(project_types or []),
            "generation_type": GENERATION_TYPE_ARCHITECTURE,
            "original_user_input": original_user_input,
            "generated_prompt": prompt,
            "model": model_name,
            "parameters": self._model_parameters(),
            "timestamp": _utc_iso(),
        }

    def build_response_payload(
        self,
        *,
        generation_id: str,
        project_id: str,
        model_name: str,
        raw_ai_response: str | None = None,
        parsed_response: dict[str, Any] | None = None,
        validation_result: dict[str, Any] | None = None,
        errors: list[str] | None = None,
        duration_seconds: float | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        return {
            "generation_id": generation_id,
            "request_id": generation_id,
            "project_id": project_id,
            "model": model_name,
            "raw_ai_response": raw_ai_response,
            "parsed_response": parsed_response,
            "validation_result": validation_result,
            "errors": errors,
            "timestamp": timestamp or _utc_iso(),
            "duration_seconds": duration_seconds,
        }

    def save_request(self, generation_id: str, payload: dict[str, Any]) -> str:
        key = self._object_key(generation_id, GENERATION_REQUEST_FILENAME)
        return self._ensure_storage().write_json(key, payload)

    def save_response(self, generation_id: str, payload: dict[str, Any]) -> str:
        key = self._object_key(generation_id, GENERATION_RESPONSE_FILENAME)
        return self._ensure_storage().write_json(key, payload)

    def upload_artifacts(
        self,
        *,
        generation_id: str,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> None:
        """Persist both generation artifacts, best-effort.

        Intended to run as a background task after the response has been sent, so
        a storage failure must never propagate to the user request. Each write is
        isolated and failures are logged (with stack trace) but swallowed.
        """

        try:
            uri = self.save_request(generation_id, request_payload)
            logger.info(
                "uploaded generation request artifact generation_id=%s uri=%s",
                generation_id,
                uri,
            )
        except Exception:
            logger.exception(
                "generation request.json upload failed generation_id=%s",
                generation_id,
            )

        try:
            uri = self.save_response(generation_id, response_payload)
            logger.info(
                "uploaded generation response artifact generation_id=%s uri=%s",
                generation_id,
                uri,
            )
        except Exception:
            logger.exception(
                "generation response.json upload failed generation_id=%s",
                generation_id,
            )

    def _ensure_storage(self) -> StorageClient:
        if self._storage is None:
            self._storage = StorageClientFactory.create_gcs(GENERATION_ARTIFACT_BUCKET)
        return self._storage

    @staticmethod
    def resolve_model_name() -> str:
        from app.config.settings import Settings

        runtime_settings = Settings()
        if runtime_settings.use_static_ai_response:
            return "static"
        return runtime_settings.openai_model

    @staticmethod
    def _object_key(generation_id: str, filename: str) -> str:
        return "/".join(
            (
                GENERATION_STORAGE_PREFIX,
                generation_id,
                filename,
            )
        )

    @staticmethod
    def _model_parameters() -> dict[str, Any]:
        return {
            "temperature": AI_TEMPERATURE,
            "response_format": AI_RESPONSE_FORMAT,
            "system_prompt": AI_SYSTEM_PROMPT,
            "use_static_ai_response": settings.use_static_ai_response,
        }

    @staticmethod
    def _original_user_input(project: Project) -> dict[str, Any]:
        answers = project.answers
        requirements = {
            key: getattr(answers, key, False) if answers else False for key in REQUIREMENT_KEYS
        }
        return {
            "name": project.name,
            "description": project.description or "",
            "project_types": list(project.project_types or []),
            "stage": project.stage,
            "expected_users": project.expected_users,
            "requirements": requirements,
        }


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
