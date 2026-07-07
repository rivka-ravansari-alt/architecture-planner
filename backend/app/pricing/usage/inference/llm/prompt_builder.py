"""Build LLM prompts from UsageContext."""

from __future__ import annotations

from app.config.params import (
    EXPECTED_USERS_LABELS,
    PROMPT_STAGE_GUIDANCE_MVP,
    PROMPT_STAGE_GUIDANCE_PRODUCTION,
    PROMPT_USAGE_ASSUMPTIONS_TEMPLATE,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
)
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.azure.registry import get_azure_pricing_model
from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.schemas import UsageInputDefinition
from app.pricing.usage.protocols import UsageAssumptionsPromptBuilder
from app.pricing.usage.schemas import ComponentUsageContext, UsageContext
from app.pricing.usage.storage_model import RDS_ENTITY_SUGGESTIONS, S3_CATEGORY_SUGGESTIONS


class LLMUsageAssumptionsPromptBuilder(UsageAssumptionsPromptBuilder):
    """Serialize UsageContext and per-component behavioral input schemas for the LLM."""

    def build(self, context: UsageContext) -> str:
        requirement_lines = self._format_requirements(context)
        stage_label = STAGE_LABELS.get(context.stage, context.stage)
        expected_users_label = EXPECTED_USERS_LABELS.get(
            context.expected_users_label,
            str(context.expected_users),
        )
        component_sections = "\n\n".join(
            self._format_component_section(component) for component in context.components
        )

        return PROMPT_USAGE_ASSUMPTIONS_TEMPLATE.format(
            product_name=context.product_name,
            description=context.description or "(not provided)",
            stage_label=stage_label,
            expected_users_label=expected_users_label,
            expected_users=context.expected_users,
            architecture_summary=context.architecture_summary or "(not provided)",
            requirement_lines="\n".join(requirement_lines),
            stage_guidance=self._stage_guidance(context.stage),
            component_sections=component_sections,
        )

    def _format_component_section(self, component: ComponentUsageContext) -> str:
        tag = "optional" if component.optional else "required"
        behavioral_lines = [
            self._format_input_definition(input_def, label="per-user behavioral")
            for input_def in component.behavioral_inputs
        ]
        config_lines = self._format_config_inputs(component)
        provider_label = component.cloud.provider
        sections = [
            f"### {component.component_id} ({component.name})",
            f"- component_id: {component.component_id}",
            f"- component_type: {component.component_type}",
            f"- status: {tag}",
            f"- {provider_label}_service: {component.cloud.pricing_model_id}",
            f"- reason: {component.reason or '(no description)'}",
            "Per-user behavioral inputs (infer for ONE user — do NOT multiply by user count):",
            *behavioral_lines,
        ]
        if config_lines:
            sections.extend(
                [
                    "Configuration inputs (not scaled by user count):",
                    *config_lines,
                ]
            )
        storage_section = self._format_storage_model_section(component)
        if storage_section:
            sections.extend(storage_section)
        return "\n".join(sections)

    def _format_storage_model_section(
        self,
        component: ComponentUsageContext,
    ) -> list[str]:
        if component.component_type == "database":
            entities = ", ".join(RDS_ENTITY_SUGGESTIONS)
            return [
                "",
                "Storage model (REQUIRED — do NOT put storage_gb_per_user in assumptions):",
                "Provide storage_model with entity-level RDS breakdown for THIS application.",
                f"Consider entities such as: {entities}.",
                "Include only entities that exist in this app's data model.",
                "For each entity: records_per_user_per_month, average_record_size_kb, "
                "retention_months, reasoning.",
                "Set backup_retention_days (MVP typically 7; production 14–35).",
                "Backup storage is computed from entity totals × retention — do not guess backup GB.",
            ]
        if component.component_type == "object_storage":
            categories = ", ".join(S3_CATEGORY_SUGGESTIONS)
            return [
                "",
                "Storage model (REQUIRED — do NOT put storage_gb_per_user in assumptions):",
                "Provide storage_model with S3 category breakdown for THIS application.",
                f"Consider categories: {categories}.",
                "Use scaling=static for shared assets (logos, JS bundles) with total_storage_gb "
                "(does NOT scale with users).",
                "Use scaling=per_user for user-owned content with storage_gb_per_user or "
                "records_per_user_per_month × average_object_size_kb × retention_months.",
                "If file_upload=false, user_uploads and media_documents must be zero.",
                "Summarize writes_per_user_per_month and reads_per_user_per_month per category.",
            ]
        return []

    def _format_config_inputs(self, component: ComponentUsageContext) -> list[str]:
        if not component.config_input_keys:
            return []
        model = (
            get_aws_pricing_model(component.cloud.pricing_model_id)
            or get_azure_pricing_model(component.cloud.pricing_model_id)
            or get_gcp_pricing_model(component.cloud.pricing_model_id)
        )
        if model is None:
            return []
        input_defs = {
            item.key: item
            for item in model.pricing_model.required_inputs
            if item.key in component.config_input_keys
        }
        return [
            self._format_input_definition(input_defs[key], label="config")
            for key in sorted(input_defs)
        ]

    @staticmethod
    def _format_input_definition(
        input_def: UsageInputDefinition,
        *,
        label: str,
    ) -> str:
        bounds: list[str] = []
        if input_def.min_value is not None:
            bounds.append(f"min={input_def.min_value}")
        if input_def.max_value is not None:
            bounds.append(f"max={input_def.max_value}")
        bound_text = f" ({', '.join(bounds)})" if bounds else ""
        required_text = "required" if input_def.required else "optional"
        return (
            f"  - {input_def.key} [{input_def.data_type.value}, {required_text}, {label}]: "
            f"{input_def.description} (unit: {input_def.unit}){bound_text}"
        )

    @staticmethod
    def _format_requirements(context: UsageContext) -> list[str]:
        return [
            f"- {REQUIREMENT_LABELS[key]}: {'Yes' if value else 'No'}"
            for key, value in context.requirements.items()
        ]

    @staticmethod
    def _stage_guidance(stage: str) -> str:
        if stage == "production":
            return PROMPT_STAGE_GUIDANCE_PRODUCTION
        return PROMPT_STAGE_GUIDANCE_MVP
