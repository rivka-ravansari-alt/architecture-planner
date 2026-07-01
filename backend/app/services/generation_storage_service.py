"""Persists AI generation request/response JSON to object storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.clients.storage_client import StorageClient, StorageClientFactory
from app.config.params import (
    AI_RESPONSE_FORMAT,
    AI_SYSTEM_PROMPT,
    AI_TEMPERATURE,
    GENERATION_REQUEST_FILENAME,
    GENERATION_RESPONSE_FILENAME,
    GENERATION_STORAGE_PREFIX,
    GENERATION_TYPE_ARCHITECTURE,
    REQUIREMENT_KEYS,
)
from app.models import Project


class GenerationStorageService:
    def __init__(self, storage: StorageClient | None = None) -> None:
        self._storage = storage or StorageClientFactory.create()

    def build_request_payload(
        self,
        project: Project,
        *,
        generation_id: str,
        prompt: str,
        model_name: str,
    ) -> dict[str, Any]:
        return {
            "generation_id": generation_id,
            "request_id": generation_id,
            "project_id": project.id,
            "user_id": project.user_id,
            "project_type": list(project.project_types or []),
            "generation_type": GENERATION_TYPE_ARCHITECTURE,
            "original_user_input": self._original_user_input(project),
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
        return self._storage.write_json(key, payload)

    def save_response(self, generation_id: str, payload: dict[str, Any]) -> str:
        key = self._object_key(generation_id, GENERATION_RESPONSE_FILENAME)
        return self._storage.write_json(key, payload)

    @staticmethod
    def resolve_model_name() -> str:
        from app.config.settings import Settings

        return Settings().openai_model

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
        }

    @staticmethod
    def _original_user_input(project: Project) -> dict[str, Any]:
        answers = project.answers
        requirements = {
            key: getattr(answers, key, False) if answers else False for key in REQUIREMENT_KEYS
        }
        usage_profile = dict(answers.usage_profile) if answers and answers.usage_profile else None
        return {
            "name": project.name,
            "description": project.description or "",
            "project_types": list(project.project_types or []),
            "stage": project.stage,
            "expected_users": project.expected_users,
            "requirements": requirements,
            "usage_profile": usage_profile,
        }


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
