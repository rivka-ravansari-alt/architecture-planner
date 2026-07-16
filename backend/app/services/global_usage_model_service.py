"""OpenAI-backed global usage model estimation (Step 3).

Single responsibility: given the application input, selected components, and
the required usage parameters, build the prompt, call OpenAI, and return a
validated ``GlobalUsageModelEstimateResult`` (prompt, raw response, and validated
usage model). It does not touch Firestore or HTTP.
"""

from __future__ import annotations

import logging
from typing import Any

from app.clients.ai_client import BaseAIClient
from app.core.exceptions import AIValidationError
from app.schemas.global_usage_model import (
    GlobalUsageModelEstimateResult,
    GlobalUsageModelResult,
    UsageParameterEstimate,
)
from app.services.global_usage_prompt_builder import GlobalUsagePromptBuilder
from app.validators.global_usage_validator import (
    fill_inapplicable_cosmos_defaults,
    parse_global_usage_model,
    required_usage_parameters,
    validate_against_parameters,
    validate_parameter_semantics,
)

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3

_CORRECTION_TEMPLATE = (
    "\n\n## Correction\n"
    "Your previous response was rejected for this reason: {error}\n"
    "Re-output the complete JSON. Return every requested usage parameter "
    "exactly once with a valid value and a short reason. "
    "Numeric parameters must be non-negative numbers. "
    "String enum parameters must use one of the allowed string values exactly. "
    "Do not add or omit parameters."
)

_MISSING_ONLY_TEMPLATE = (
    "\n\n## Missing parameters\n"
    "Some parameters were already captured. Return JSON that includes ONLY these "
    "still-missing usage parameters (each with value and reason):\n"
    "{missing_parameters}\n"
    "Do not omit any of them. Numeric parameters must be non-negative numbers. "
    "String enum parameters must use one of the allowed string values exactly."
)


class GlobalUsageModelService:
    def __init__(
        self,
        ai_client: BaseAIClient,
        prompt_builder: GlobalUsagePromptBuilder | None = None,
        *,
        max_attempts: int = _MAX_ATTEMPTS,
    ) -> None:
        self._ai_client = ai_client
        self._prompt_builder = prompt_builder or GlobalUsagePromptBuilder()
        self._max_attempts = max(1, max_attempts)

    def estimate(
        self,
        *,
        application_description: str,
        platform: str,
        stage: str,
        expected_users: int,
        requirements: dict[str, Any],
        selected_components: list[dict[str, Any]],
        usage_parameters: list[str],
        static_usage_values: dict[str, Any] | None = None,
    ) -> GlobalUsageModelEstimateResult:
        requested = [
            parameter.strip()
            for parameter in usage_parameters
            if isinstance(parameter, str) and parameter.strip()
        ]
        base_prompt = self._prompt_builder.build(
            application_description=application_description,
            platform=platform,
            stage=stage,
            expected_users=expected_users,
            requirements=requirements,
            selected_components=selected_components,
            usage_parameters=requested,
            static_usage_values=static_usage_values,
        )

        accumulated: dict[str, UsageParameterEstimate] = {}
        last_error: AIValidationError | None = None
        last_prompt = base_prompt
        last_raw_response = ""

        for attempt in range(1, self._max_attempts + 1):
            capacity_mode = None
            if "capacity_mode" in accumulated:
                mode_value = accumulated["capacity_mode"].value
                capacity_mode = mode_value if isinstance(mode_value, str) else None
            required = required_usage_parameters(
                requested, capacity_mode=capacity_mode
            )
            missing = [
                parameter for parameter in required if parameter not in accumulated
            ]
            if not missing:
                break

            if attempt == 1:
                prompt = base_prompt
            elif accumulated:
                prompt = base_prompt + _MISSING_ONLY_TEMPLATE.format(
                    missing_parameters="\n".join(f"- {parameter}" for parameter in missing)
                )
            else:
                prompt = base_prompt + _CORRECTION_TEMPLATE.format(
                    error=(
                        last_error.message
                        if last_error is not None
                        else "Previous response was invalid."
                    )
                )

            raw_response = self._ai_client.generate(prompt)
            last_prompt = prompt
            last_raw_response = raw_response

            try:
                partial = parse_global_usage_model(raw_response)
            except AIValidationError as error:
                last_error = error
                logger.warning(
                    "global_usage_model parse failed (attempt %d/%d): %s",
                    attempt,
                    self._max_attempts,
                    error.message,
                )
                continue

            accepted = 0
            for parameter, estimate in partial.usage.items():
                if parameter not in requested or parameter in accumulated:
                    continue
                try:
                    validate_parameter_semantics(
                        GlobalUsageModelResult(usage={parameter: estimate}),
                        [parameter],
                    )
                except AIValidationError as error:
                    last_error = error
                    logger.warning(
                        "global_usage_model rejected %s (attempt %d/%d): %s",
                        parameter,
                        attempt,
                        self._max_attempts,
                        error.message,
                    )
                    continue
                accumulated[parameter] = estimate
                accepted += 1

            capacity_mode = None
            if "capacity_mode" in accumulated:
                mode_value = accumulated["capacity_mode"].value
                capacity_mode = mode_value if isinstance(mode_value, str) else None
            still_missing = [
                parameter
                for parameter in required_usage_parameters(
                    requested, capacity_mode=capacity_mode
                )
                if parameter not in accumulated
            ]
            if still_missing:
                last_error = AIValidationError(
                    "Usage parameters missing from the response: "
                    + ", ".join(still_missing)
                    + "."
                )
                logger.warning(
                    "global_usage_model incomplete (attempt %d/%d): accepted=%d missing=%d",
                    attempt,
                    self._max_attempts,
                    accepted,
                    len(still_missing),
                )

        result = fill_inapplicable_cosmos_defaults(
            GlobalUsageModelResult(usage=accumulated),
            requested,
        )
        try:
            validate_against_parameters(result, requested)
            validate_parameter_semantics(result, requested)
        except AIValidationError as error:
            raise error from last_error

        logger.info(
            "global_usage_model parameters=%d attempts_used<=%d",
            len(result.usage),
            self._max_attempts,
        )
        return GlobalUsageModelEstimateResult(
            result=result,
            prompt=last_prompt,
            raw_response=last_raw_response,
        )
