"""Call the configured AI model for architecture generation."""

from __future__ import annotations

from openai import OpenAI

from ..config import settings
from .static_ai_response import build_static_ai_response


class AIClientError(RuntimeError):
    """Raised when the AI provider call fails."""


def generate_architecture(prompt: str) -> str:
    if settings.use_static_ai_response:
        return build_static_ai_response(prompt)

    if not settings.openai_api_key:
        raise AIClientError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in backend/.env."
        )

    client = OpenAI(api_key=settings.openai_api_key)

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
        raise AIClientError(f"AI request failed: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise AIClientError("AI returned an empty response.")
    return content
