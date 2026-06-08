"""AI provider clients for architecture generation."""

from __future__ import annotations

import json
import logging
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
from app.core.exceptions import AIClientError
from app.core.logging import AIClientLogger

logger = logging.getLogger(__name__)

_MODELS_USING_MAX_COMPLETION_TOKENS = ("gpt-5", "o1", "o3", "o4")


def _completion_limit_kwargs(model: str, max_output_tokens: int) -> dict[str, int]:
    model_lower = model.strip().lower()
    if any(model_lower.startswith(prefix) for prefix in _MODELS_USING_MAX_COMPLETION_TOKENS):
        return {"max_completion_tokens": max_output_tokens}
    return {"max_tokens": max_output_tokens}


class BaseAIClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return raw JSON text from the AI provider."""


class StaticAIClient(BaseAIClient):
    def __init__(self, logger: AIClientLogger | None = None) -> None:
        self._logger = logger or AIClientLogger()

    def generate(self, prompt: str) -> str:
        self._logger.log_started("load_static")
        content = json.dumps(STATIC_AI_PAYLOAD)
        self._logger.log_completed("load_static", response_chars=len(content))
        return content


class OpenAIClient(BaseAIClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout_seconds: float = 120.0,
        max_output_tokens: int = 8000,
        logger: AIClientLogger | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model = model
        self._max_output_tokens = max_output_tokens
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
                **_completion_limit_kwargs(self._model, self._max_output_tokens),
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
    @staticmethod
    def create() -> BaseAIClient:
        # Read settings fresh so local .env changes apply without a full server restart.
        from app.config.settings import Settings

        runtime_settings = Settings()

        if runtime_settings.use_static_ai_response:
            logger.info("Using static AI client (USE_STATIC_AI_RESPONSE=true).")
            return StaticAIClient()
        if not runtime_settings.openai_api_key:
            raise AIClientError(ERR_OPENAI_KEY_MISSING)
        logger.info("Using OpenAI client model=%s.", runtime_settings.openai_model)
        return OpenAIClient(
            runtime_settings.openai_api_key,
            runtime_settings.openai_model,
            timeout_seconds=runtime_settings.openai_request_timeout_seconds,
            max_output_tokens=runtime_settings.openai_max_output_tokens,
        )
