"""Validate shared LLM usage-assumption responses."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.exceptions import AIValidationError
from app.pricing.assumptions import coerce_value
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption, UsageInputDefinition
from app.pricing.usage.component_type_behavioral_models import get_component_type_behavioral_model
from app.pricing.usage.shared.prompt_builder import SharedUsageAssumptionsPromptBuilder
from app.pricing.usage.shared.schemas import (
    SharedComponentInference,
    SharedComponentUsageContext,
    SharedUsageContext,
    SharedUsageInferenceResult,
)
from app.pricing.usage.storage_model import (
    inject_rds_storage_into_behavioral,
    inject_s3_storage_into_behavioral,
    parse_rds_storage_model,
    parse_s3_storage_model,
)
from app.pricing.usage.schemas import UsageInferenceAudit

_STORAGE_DERIVED_KEYS = frozenset(
    {
        "storage_gb_per_user",
        "backup_storage_gb_per_user",
        "writes_per_user_per_month",
        "reads_per_user_per_month",
        "avg_download_size_kb",
        "static_storage_gb",
    }
)


class SharedUsageAssumptionsResponseValidator:
    """Parse and validate cloud-agnostic LLM behavioral usage JSON."""

    def validate(self, raw: str, context: SharedUsageContext) -> SharedUsageInferenceResult:
        payload = self._parse_json(raw)
        if "components" not in payload:
            raise AIValidationError("Missing required field: components")

        components_by_id = {item.component_id: item for item in context.components}
        if not components_by_id:
            raise AIValidationError("No mapped components to validate.")

        llm_components = payload["components"]
        if not isinstance(llm_components, list) or not llm_components:
            raise AIValidationError("components must be a non-empty array")

        results: list[SharedComponentInference] = []
        seen_ids: set[str] = set()

        for entry in llm_components:
            if not isinstance(entry, dict):
                raise AIValidationError("Each components entry must be an object")

            component_id = entry.get("component_id")
            if not component_id or not isinstance(component_id, str):
                raise AIValidationError("Each component entry requires component_id")

            if component_id in seen_ids:
                raise AIValidationError(f"Duplicate component_id: {component_id}")
            seen_ids.add(component_id)

            component_ctx = components_by_id.get(component_id)
            if component_ctx is None:
                raise AIValidationError(f"Unknown component_id: {component_id}")

            assumptions_raw = entry.get("assumptions")
            if not isinstance(assumptions_raw, list):
                raise AIValidationError(f"Component {component_id} missing assumptions array")

            self._reject_storage_derived_keys(component_id, assumptions_raw)

            behavioral, config = self._build_inferred_assumptions(
                component_id,
                component_ctx,
                assumptions_raw,
            )
            storage_breakdown = self._apply_storage_model(
                entry,
                component_ctx,
                behavioral,
                config,
                context,
            )
            results.append(
                SharedComponentInference(
                    component_id=component_ctx.component_id,
                    order=component_ctx.order,
                    component_type=component_ctx.component_type,
                    behavioral=behavioral,
                    config=config,
                    storage_breakdown=storage_breakdown,
                )
            )

        missing_components = set(components_by_id.keys()) - seen_ids
        if missing_components:
            raise AIValidationError(
                "LLM response missing components: " + ", ".join(sorted(missing_components))
            )

        sorted_results = tuple(sorted(results, key=lambda item: item.order))
        return SharedUsageInferenceResult(
            components=sorted_results,
            inference_source="llm",
            audit=UsageInferenceAudit(raw_response=raw),
        )

    def _build_inferred_assumptions(
        self,
        component_id: str,
        component_ctx: SharedComponentUsageContext,
        assumptions_raw: list[Any],
    ) -> tuple[dict[str, UsageAssumption], dict[str, UsageAssumption]]:
        input_defs = self._input_definitions(component_ctx)
        behavioral: dict[str, UsageAssumption] = {}
        config: dict[str, UsageAssumption] = {}

        for item in assumptions_raw:
            if not isinstance(item, dict):
                raise AIValidationError(
                    f"Component {component_id}: each assumption must be an object"
                )

            key = item.get("key")
            if not key or not isinstance(key, str):
                raise AIValidationError(f"Component {component_id}: assumption missing key")

            if key in behavioral or key in config:
                raise AIValidationError(
                    f"Component {component_id}: duplicate assumption key {key}"
                )

            input_def = input_defs.get(key)
            if input_def is None:
                raise AIValidationError(
                    f"Component {component_id}: unknown assumption key {key!r}"
                )

            if "value" not in item:
                raise AIValidationError(
                    f"Component {component_id}: assumption {key} missing value"
                )

            value = self._coerce_and_clamp(item["value"], input_def, component_id, key)
            unit = item.get("unit") or input_def.unit
            confidence = self._parse_confidence(item.get("confidence"), component_id, key)
            reasoning = item.get("reasoning")
            if not reasoning or not isinstance(reasoning, str) or not reasoning.strip():
                raise AIValidationError(
                    f"Component {component_id}: assumption {key} requires non-empty reasoning"
                )

            assumption = UsageAssumption(
                key=key,
                value=value,
                unit=unit,
                source=AssumptionSource.inferred,
                confidence=confidence,
                reasoning=reasoning.strip(),
            )
            if key in component_ctx.config_input_keys:
                config[key] = assumption
            else:
                behavioral[key] = assumption

        self._validate_required_inputs(component_id, component_ctx, behavioral, config)
        return behavioral, config

    def _apply_storage_model(
        self,
        entry: dict[str, Any],
        component_ctx: SharedComponentUsageContext,
        behavioral: dict[str, UsageAssumption],
        config: dict[str, UsageAssumption],
        context: SharedUsageContext,
    ) -> list[UsageAssumption]:
        component_type = component_ctx.component_type
        if component_type not in {"database", "object_storage"}:
            return []

        storage_model = entry.get("storage_model")
        if storage_model is None:
            raise AIValidationError(
                f"Component {component_ctx.component_id}: storage_model is required for "
                f"{component_type} components."
            )

        if component_type == "database":
            derivation = parse_rds_storage_model(
                storage_model,
                component_id=component_ctx.component_id,
            )
            return inject_rds_storage_into_behavioral(behavioral, derivation)

        file_upload = context.requirements.get("file_upload", False) or context.feature_flags.get(
            "file_upload", False
        )
        derivation = parse_s3_storage_model(
            storage_model,
            component_id=component_ctx.component_id,
            file_upload=file_upload,
        )
        return inject_s3_storage_into_behavioral(behavioral, config, derivation)

    @staticmethod
    def _input_definitions(
        component_ctx: SharedComponentUsageContext,
    ) -> dict[str, UsageInputDefinition]:
        defs = {item.key: item for item in component_ctx.behavioral_inputs}
        for key in component_ctx.config_input_keys:
            input_def = SharedUsageAssumptionsPromptBuilder._config_input_definition(key)
            if input_def is not None:
                defs[key] = input_def
        return defs

    @staticmethod
    def _validate_required_inputs(
        component_id: str,
        component_ctx: SharedComponentUsageContext,
        behavioral: dict[str, UsageAssumption],
        config: dict[str, UsageAssumption],
    ) -> None:
        model = get_component_type_behavioral_model(component_ctx.component_type)
        if model is None:
            return
        for input_def in model.behavioral_inputs:
            if input_def.required and input_def.key not in behavioral:
                raise AIValidationError(
                    f"Component {component_id} missing required behavioral assumption: "
                    f"{input_def.key}"
                )

    @staticmethod
    def _reject_storage_derived_keys(
        component_id: str,
        assumptions_raw: list[Any],
    ) -> None:
        for item in assumptions_raw:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            if key in _STORAGE_DERIVED_KEYS:
                raise AIValidationError(
                    f"Component {component_id}: {key!r} must come from storage_model, "
                    "not the assumptions array."
                )

    @staticmethod
    def _coerce_and_clamp(
        raw: Any,
        input_def: UsageInputDefinition,
        component_id: str,
        key: str,
    ) -> int | float | str | bool:
        try:
            value = coerce_value(raw, input_def)
        except (TypeError, ValueError) as exc:
            raise AIValidationError(
                f"Component {component_id}: invalid value for {key}: {exc}"
            ) from exc

        if isinstance(value, (int, float)):
            if input_def.min_value is not None and value < input_def.min_value:
                value = input_def.min_value
            if input_def.max_value is not None and value > input_def.max_value:
                value = input_def.max_value
        return value

    @staticmethod
    def _parse_confidence(
        raw: Any,
        component_id: str,
        key: str,
    ) -> AssumptionConfidence:
        if raw is None:
            return AssumptionConfidence.medium
        if not isinstance(raw, str):
            raise AIValidationError(
                f"Component {component_id}: assumption {key} confidence must be a string"
            )
        normalized = raw.strip().lower()
        try:
            return AssumptionConfidence(normalized)
        except ValueError as exc:
            raise AIValidationError(
                f"Component {component_id}: assumption {key} has invalid confidence {raw!r}"
            ) from exc

    def _parse_json(self, raw: str) -> dict[str, Any]:
        if not raw or not raw.strip():
            raise AIValidationError("AI response was empty")
        text = self._extract_json(raw)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIValidationError(f"AI response is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise AIValidationError("AI response must be a JSON object")
        return payload

    @staticmethod
    def _extract_json(raw: str) -> str:
        stripped = raw.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped
