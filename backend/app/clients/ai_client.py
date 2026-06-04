"""AI provider clients for architecture generation."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from openai import OpenAI

from app.clients.static_payload import STATIC_AI_PAYLOAD
from app.config.params import (
    AI_RESPONSE_FORMAT,
    AI_SYSTEM_PROMPT,
    AI_TEMPERATURE,
    ERR_AI_EMPTY_RESPONSE,
    ERR_OPENAI_KEY_MISSING,
)
from app.config.settings import settings
from app.core.exceptions import AIClientError
from app.core.logging import AIClientLogger


class BaseAIClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return raw JSON text from the AI provider."""


class StaticAIClient(BaseAIClient):
    """Returns canned architecture JSON for local development."""

    def __init__(self, logger: AIClientLogger | None = None) -> None:
        self._logger = logger or AIClientLogger()

    def generate(self, prompt: str) -> str:
        self._logger.log_started("load_static")
        content = json.dumps(STATIC_AI_PAYLOAD)
        self._logger.log_completed("load_static", response_chars=len(content))
        return content


class OpenAIClient(BaseAIClient):
    """Calls OpenAI Chat Completions with JSON response format."""

    def __init__(
        self,
        api_key: str,
        model: str,
        logger: AIClientLogger | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._logger = logger or AIClientLogger()

    def generate(self, prompt: str) -> str:
        self._logger.log_started("openai_request", model=self._model, prompt_chars=len(prompt))
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=AI_RESPONSE_FORMAT,
                temperature=AI_TEMPERATURE,
            )
        except Exception as exc:  # noqa: BLE001
            reason = f"AI request failed: {exc}"
            self._logger.log_failed("openai_request", reason, prompt)
            raise AIClientError(reason) from exc

        content = response.choices[0].message.content
        if not content:
            self._logger.log_failed("openai_response", ERR_AI_EMPTY_RESPONSE, prompt)
            raise AIClientError(ERR_AI_EMPTY_RESPONSE)

        self._logger.log_completed("openai_response", response_chars=len(content))
        return content


class AIClientFactory:
    """Selects the configured AI client implementation."""

    @staticmethod
    def create() -> BaseAIClient:
        if settings.use_static_ai_response:
            return StaticAIClient()
        if not settings.openai_api_key:
            raise AIClientError(ERR_OPENAI_KEY_MISSING)
        return OpenAIClient(settings.openai_api_key, settings.openai_model)
