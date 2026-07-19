"""OpenAI-backed architecture component selection (Step 2).

Single responsibility: given the application input and the categories loaded
from Firestore, build the prompt, call OpenAI, and return a validated
``ComponentSelectionResult``. It does not touch Firestore or HTTP concerns.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.clients.ai_client import BaseAIClient
from app.config.params import COMPONENT_SELECTION_SYSTEM_PROMPT
from app.core.exceptions import AIValidationError
from app.schemas.component_selection import ComponentSelectionResult
from app.services.component_selection_prompt_builder import (
    ComponentSelectionPromptBuilder,
)
from app.validators.component_selection_validator import parse_and_validate


logger = logging.getLogger(__name__)

# Bounded retry: LLMs occasionally omit or duplicate a category. Rather than
# silently repairing the output, we re-ask the model with its own validation
# error and let it correct itself. After the last attempt the error surfaces.
_MAX_ATTEMPTS = 3

_CORRECTION_TEMPLATE = (
    "\n\n## Correction\n"
    "Your previous response was rejected for this reason: {error}\n"
    "Re-output the complete JSON. Classify every category id exactly once, "
    "across 'selected' and 'excluded' combined. Do not omit, duplicate, or "
    "invent any id. Use only ids from the Available architecture categories "
    "section — never business requirement names."
)


@dataclass
class GenerationTrace:
    """Mutable record of a single selection run, used to build generation artifacts.

    ``select`` fills this in on success so callers can persist the exact prompt
    and raw model output without changing the method's return contract.
    """

    prompt: str | None = None
    raw_response: str | None = None
    duration_seconds: float | None = None
    attempts: int = 0


class ArchitectureComponentSelectionService:
    def __init__(
        self,
        ai_client: BaseAIClient,
        prompt_builder: ComponentSelectionPromptBuilder | None = None,
        *,
        max_attempts: int = _MAX_ATTEMPTS,
    ) -> None:
        self._ai_client = ai_client
        self._prompt_builder = prompt_builder or ComponentSelectionPromptBuilder()
        self._max_attempts = max(1, max_attempts)

    def select(
        self,
        *,
        application_description: str,
        platform: str,
        stage: str,
        expected_users: int,
        requirements: dict[str, Any],
        categories: list[dict[str, Any]],
        record: GenerationTrace | None = None,
    ) -> ComponentSelectionResult:
        """Build the prompt, call OpenAI, and return the validated selection.

        Retries a bounded number of times on validation failure, feeding the
        model its own error so it can self-correct. Never repairs the payload.

        When ``record`` is provided, it is populated on success with the final
        prompt, raw model response, attempt count, and duration so the caller can
        persist generation artifacts.
        """

        started_at = time.perf_counter()
        base_prompt = self._prompt_builder.build(
            application_description=application_description,
            platform=platform,
            stage=stage,
            expected_users=expected_users,
            requirements=requirements,
            categories=categories,
        )
        category_ids = [category["id"] for category in categories]

        last_error: AIValidationError | None = None
        prompt = base_prompt
        for attempt in range(1, self._max_attempts + 1):
            raw_response = self._ai_client.generate(
                prompt,
                system_prompt=COMPONENT_SELECTION_SYSTEM_PROMPT,
            )
            try:
                result = parse_and_validate(raw_response, category_ids)
            except AIValidationError as error:
                last_error = error
                logger.warning(
                    "component_selection validation failed (attempt %d/%d): %s",
                    attempt,
                    self._max_attempts,
                    error.message,
                )
                prompt = base_prompt + _CORRECTION_TEMPLATE.format(error=error.message)
                continue

            if record is not None:
                record.prompt = prompt
                record.raw_response = raw_response
                record.attempts = attempt
                record.duration_seconds = time.perf_counter() - started_at

            logger.info(
                "component_selection selected=%d excluded=%d (attempt %d)",
                len(result.selected),
                len(result.excluded),
                attempt,
            )
            return result

        assert last_error is not None
        raise last_error
