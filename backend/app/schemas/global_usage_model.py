"""Pydantic models for the global usage model step (Step 3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

StaticUsageValue = str | int | float


class UsageParameterEstimate(BaseModel):
    """A single LLM-estimated behavioral usage parameter."""

    model_config = ConfigDict(extra="forbid")

    value: float | str
    reason: str

    @field_validator("value")
    @classmethod
    def _validate_value(cls, value: float | str) -> float | str:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("must be a non-empty string")
            return stripped
        numeric = float(value)
        if numeric < 0:
            raise ValueError("must be non-negative")
        return numeric

    @field_validator("reason")
    @classmethod
    def _non_empty_reason(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()


class GlobalUsageModelResult(BaseModel):
    """The validated OpenAI output (behavioral estimates only)."""

    model_config = ConfigDict(extra="forbid")

    usage: dict[str, UsageParameterEstimate]


class GlobalUsageModelEstimateResult(BaseModel):
    """Validated LLM output plus the exact prompt and raw response that produced it."""

    model_config = ConfigDict(extra="forbid")

    result: GlobalUsageModelResult
    prompt: str
    raw_response: str


class GlobalUsageModelPayload(BaseModel):
    """Combined LLM estimates and project-backed static values."""

    model_config = ConfigDict(extra="forbid")

    llm: dict[str, UsageParameterEstimate]
    static: dict[str, StaticUsageValue]


class GlobalUsageModelResponse(BaseModel):
    """The global usage model returned by the generate / get endpoints."""

    model_id: str
    selection_id: str
    llm_parameters: list[str]
    static_parameters: list[str]
    llm: dict[str, UsageParameterEstimate]
    static: dict[str, StaticUsageValue]

    @classmethod
    def from_payload(
        cls,
        *,
        model_id: str,
        selection_id: str,
        llm_parameters: list[str],
        static_parameters: list[str],
        payload: GlobalUsageModelPayload,
    ) -> GlobalUsageModelResponse:
        return cls(
            model_id=model_id,
            selection_id=selection_id,
            llm_parameters=llm_parameters,
            static_parameters=static_parameters,
            llm=payload.llm,
            static=payload.static,
        )

    @classmethod
    def from_stored_document(cls, document: dict[str, Any]) -> GlobalUsageModelResponse:
        usage_model = document.get("usage_model") or {}
        llm_payload = usage_model.get("llm") or document.get("usage") or {}
        static_payload = usage_model.get("static") or document.get("static") or {}

        llm = {
            parameter: UsageParameterEstimate.model_validate(estimate)
            for parameter, estimate in llm_payload.items()
        }
        static: dict[str, StaticUsageValue] = {}
        for parameter, value in static_payload.items():
            if isinstance(value, (str, int, float)):
                static[parameter] = value

        return cls(
            model_id=document["id"],
            selection_id=document.get("selection_id", ""),
            llm_parameters=list(document.get("llm_parameters", document.get("usage_parameters", []))),
            static_parameters=list(document.get("static_parameters", [])),
            llm=llm,
            static=static,
        )
