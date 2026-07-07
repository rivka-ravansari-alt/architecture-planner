"""LLM-based usage assumption inference provider."""

from __future__ import annotations

import logging

from app.clients.ai_client import BaseAIClient
from app.config.params import USAGE_ASSUMPTIONS_SYSTEM_PROMPT
from app.core.exceptions import AIClientError, AIValidationError
from app.pricing.usage.inference.llm.prompt_builder import LLMUsageAssumptionsPromptBuilder
from app.pricing.usage.inference.llm.response_validator import LLMUsageAssumptionsResponseValidator
from app.pricing.usage.protocols import UsageInferenceProvider
from app.pricing.usage.schemas import UsageContext, UsageInferenceAudit, UsageInferenceResult

logger = logging.getLogger(__name__)


class LLMUsageInferenceProvider(UsageInferenceProvider):
    """Infer usage assumptions via a batched LLM call."""

    def __init__(
        self,
        *,
        ai_client: BaseAIClient,
        prompt_builder: LLMUsageAssumptionsPromptBuilder | None = None,
        validator: LLMUsageAssumptionsResponseValidator | None = None,
    ) -> None:
        self._ai_client = ai_client
        self._prompt_builder = prompt_builder or LLMUsageAssumptionsPromptBuilder()
        self._validator = validator or LLMUsageAssumptionsResponseValidator()

    def build_prompt(self, context: UsageContext) -> str:
        return self._prompt_builder.build(context)

    def parse_response(self, raw: str, context: UsageContext) -> UsageInferenceResult:
        result = self._validator.validate(raw, context)
        return UsageInferenceResult(
            components=result.components,
            inference_source="llm",
            audit=UsageInferenceAudit(
                raw_response=raw,
                validation_errors=result.audit.validation_errors,
            ),
        )

    def infer(self, context: UsageContext) -> UsageInferenceResult:
        prompt = self.build_prompt(context)
        raw_response = self._call_ai(prompt)
        result = self.parse_response(raw_response, context)
        return UsageInferenceResult(
            components=result.components,
            inference_source="llm",
            audit=UsageInferenceAudit(
                prompt=prompt,
                raw_response=raw_response,
            ),
        )

    def _call_ai(self, prompt: str) -> str:
        return self._ai_client.generate(prompt, system_prompt=USAGE_ASSUMPTIONS_SYSTEM_PROMPT)

    @staticmethod
    def system_prompt() -> str:
        return USAGE_ASSUMPTIONS_SYSTEM_PROMPT

    def infer_with_fallback_on_error(
        self,
        context: UsageContext,
        fallback: UsageInferenceProvider,
    ) -> UsageInferenceResult:
        prompt = self.build_prompt(context)
        try:
            raw_response = self._call_ai(prompt)
            result = self.parse_response(raw_response, context)
            return UsageInferenceResult(
                components=result.components,
                inference_source="llm",
                audit=UsageInferenceAudit(prompt=prompt, raw_response=raw_response),
            )
        except (AIClientError, AIValidationError, ValueError) as exc:
            logger.warning("LLM usage inference failed, using heuristic fallback: %s", exc)
            fallback_result = fallback.infer(context)
            return UsageInferenceResult(
                components=fallback_result.components,
                inference_source="heuristic_fallback",
                audit=UsageInferenceAudit(
                    prompt=prompt,
                    validation_errors=(str(exc),),
                ),
            )
