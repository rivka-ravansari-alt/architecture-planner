"""Validate LLM usage-assumption responses against UsageContext."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.exceptions import AIValidationError
from app.pricing.assumptions import coerce_value, resolve_usage_assumptions
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.azure.registry import get_azure_pricing_model
from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.schemas import (
    AssumptionConfidence,
    AssumptionSource,
    ComponentPricingInput,
    UsageAssumption,
    UsageInputDefinition,
)
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.protocols import PricingModelRegistry, UsageAssumptionsResponseValidator
from app.pricing.usage.storage_model import (
    inject_rds_storage_into_behavioral,
    inject_s3_storage_into_behavioral,
    parse_rds_storage_model,
    parse_s3_storage_model,
)
from app.pricing.usage.scaling import scale_behavioral_assumptions
from app.pricing.usage.schemas import ComponentUsageContext, UsageContext, UsageInferenceAudit, UsageInferenceResult

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


def _get_pricing_model(service_id: str, provider: str):
    if provider == "aws":
        return get_aws_pricing_model(service_id)
    if provider == "gcp":
        return get_gcp_pricing_model(service_id)
    return get_azure_pricing_model(service_id)


class LLMUsageAssumptionsResponseValidator(UsageAssumptionsResponseValidator):
    """Parse and validate batched LLM behavioral usage assumption JSON."""

    def __init__(
        self,
        *,
        registries: dict[str, PricingModelRegistry] | None = None,
    ) -> None:
        self._registries = registries or UsageContextBuilder()._registries

    def validate(self, raw: str, context: UsageContext) -> UsageInferenceResult:
        registry = self._registries.get(context.provider)
        if registry is None:
            raise AIValidationError(f"No pricing registry for provider {context.provider!r}.")

        payload = self._parse_json(raw)
        if "components" not in payload:
            raise AIValidationError("Missing required field: components")

        components_by_id = {item.component_id: item for item in context.components}
        if not components_by_id:
            raise AIValidationError("No mapped components to validate.")

        llm_components = payload["components"]
        if not isinstance(llm_components, list) or not llm_components:
            raise AIValidationError("components must be a non-empty array")

        results: list[ComponentPricingInput] = []
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

            model = registry.resolve_model(component_ctx.cloud.mapped_service_name)
            if model is None:
                raise AIValidationError(
                    f"Unknown pricing model for component {component_id}"
                )

            assumptions_raw = entry.get("assumptions")
            if not isinstance(assumptions_raw, list):
                raise AIValidationError(f"Component {component_id} missing assumptions array")

            self._reject_storage_derived_keys(component_id, assumptions_raw)

            behavioral, config = self._build_inferred_assumptions(
                component_id,
                component_ctx,
                assumptions_raw,
                context.provider,
            )
            storage_breakdown = self._apply_storage_model(
                entry,
                component_ctx,
                behavioral,
                config,
                context,
            )
            scaled = scale_behavioral_assumptions(
                model.service,
                behavioral=behavioral,
                config=config,
                expected_users=context.expected_users,
            )
            resolution = resolve_usage_assumptions(model, inferred=scaled)
            if not resolution.ready_for_calculation:
                missing_keys = ", ".join(item.key for item in resolution.missing)
                raise AIValidationError(
                    f"Component {component_id} missing required assumptions: {missing_keys}"
                )

            behavioral_list = list(behavioral.values()) + list(config.values()) + storage_breakdown
            results.append(
                ComponentPricingInput(
                    component_id=component_ctx.component_id,
                    order=component_ctx.order,
                    provider=context.provider,
                    cloud_service=model.service,
                    resolved=resolution.resolved,
                    behavioral_assumptions=sorted(
                        behavioral_list,
                        key=lambda item: item.key,
                    ),
                )
            )

        missing_components = set(components_by_id.keys()) - seen_ids
        if missing_components:
            raise AIValidationError(
                "LLM response missing components: " + ", ".join(sorted(missing_components))
            )

        sorted_results = tuple(sorted(results, key=lambda item: item.order))
        return UsageInferenceResult(
            components=sorted_results,
            inference_source="llm",
            audit=UsageInferenceAudit(raw_response=raw),
        )

    def _build_inferred_assumptions(
        self,
        component_id: str,
        component_ctx: ComponentUsageContext,
        assumptions_raw: list[Any],
        provider: str,
    ) -> tuple[dict[str, UsageAssumption], dict[str, UsageAssumption]]:
        input_defs = self._llm_input_definitions(component_ctx, provider)
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

        self._validate_required_inputs(component_id, component_ctx, behavioral, config, provider)
        return behavioral, config

    def _apply_storage_model(
        self,
        entry: dict[str, Any],
        component_ctx: ComponentUsageContext,
        behavioral: dict[str, UsageAssumption],
        config: dict[str, UsageAssumption],
        context: UsageContext,
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
    def _llm_input_definitions(
        component_ctx: ComponentUsageContext,
        provider: str,
    ) -> dict[str, UsageInputDefinition]:
        defs = {item.key: item for item in component_ctx.behavioral_inputs}
        pricing_model = _get_pricing_model(component_ctx.cloud.pricing_model_id, provider)
        if pricing_model is not None:
            for item in pricing_model.pricing_model.required_inputs:
                if item.key in component_ctx.config_input_keys:
                    defs[item.key] = item
        return defs

    @staticmethod
    def _validate_required_inputs(
        component_id: str,
        component_ctx: ComponentUsageContext,
        behavioral: dict[str, UsageAssumption],
        config: dict[str, UsageAssumption],
        provider: str,
    ) -> None:
        for input_def in component_ctx.behavioral_inputs:
            if input_def.required and input_def.key not in behavioral:
                raise AIValidationError(
                    f"Component {component_id} missing required behavioral assumption: "
                    f"{input_def.key}"
                )

        pricing_model = _get_pricing_model(component_ctx.cloud.pricing_model_id, provider)
        if pricing_model is None:
            return
        defaults = pricing_model.pricing_model.default_values
        for input_def in pricing_model.pricing_model.required_inputs:
            if input_def.key not in component_ctx.config_input_keys:
                continue
            if input_def.key in config:
                continue
            has_default = (
                input_def.default_value is not None or input_def.key in defaults
            )
            if has_default:
                continue
            if input_def.required:
                raise AIValidationError(
                    f"Component {component_id} missing required config assumption: "
                    f"{input_def.key}"
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
