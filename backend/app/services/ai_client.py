"""Call the configured AI model for architecture generation."""

from __future__ import annotations

import logging

from openai import OpenAI

from ..config import settings
from .static_ai_response import build_static_ai_response

logger = logging.getLogger(__name__)


class AIClientError(RuntimeError):
    """Raised when the AI provider call fails."""


def _log_openai_failure(step: str, *, reason: str, prompt: str) -> None:
    logger.error("ai_client step=%s status=failed reason=%s", step, reason)
    logger.error("ai_client step=%s status=failed request_prompt:\n%s", step, prompt)


def generate_architecture(prompt: str) -> str:
    if settings.use_static_ai_response:
        logger.info("ai_client step=load_static status=started")
        content = build_static_ai_response(prompt)
        logger.info(
            "ai_client step=load_static status=completed reason=response_chars=%s",
            len(content),
        )
        return content

    if not settings.openai_api_key:
        reason = "OpenAI API key is not configured. Set OPENAI_API_KEY in backend/.env."
        logger.error("ai_client step=check_config status=failed reason=%s", reason)
        raise AIClientError(reason)

    client = OpenAI(api_key=settings.openai_api_key)
    logger.info(
        "ai_client step=openai_request status=started reason=model=%s prompt_chars=%s",
        settings.openai_model,
        len(prompt),
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Archsari, a software architecture planning assistant. "
                        "Return only valid JSON matching the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception as exc:  # noqa: BLE001 - surface provider errors to caller
        reason = f"AI request failed: {exc}"
        _log_openai_failure("openai_request", reason=reason, prompt=prompt)
        raise AIClientError(reason) from exc

    content = response.choices[0].message.content
    if not content:
        reason = "AI returned an empty response."
        _log_openai_failure("openai_response", reason=reason, prompt=prompt)
        raise AIClientError(reason)
    logger.info(
        "ai_client step=openai_request status=completed reason=response_chars=%s",
        len(content),
    )
    return content
