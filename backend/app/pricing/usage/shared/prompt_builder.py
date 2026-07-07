"""Build shared LLM prompts from cloud-agnostic usage context."""

from __future__ import annotations

from app.config.params import (
    EXPECTED_USERS_LABELS,
    PROMPT_STAGE_GUIDANCE_MVP,
    PROMPT_STAGE_GUIDANCE_PRODUCTION,
    PROMPT_USAGE_ASSUMPTIONS_TEMPLATE,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
)
from app.pricing.schemas import UsageInputDefinition
from app.pricing.usage.shared.schemas import SharedComponentUsageContext, SharedUsageContext
from app.pricing.usage.storage_model import RDS_ENTITY_SUGGESTIONS, S3_CATEGORY_SUGGESTIONS


class SharedUsageAssumptionsPromptBuilder:
    """Serialize SharedUsageContext for one batched LLM call."""

    def build(self, context: SharedUsageContext) -> str:
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

    def _format_component_section(self, component: SharedComponentUsageContext) -> str:
        tag = "optional" if component.optional else "required"
        behavioral_lines = [
            self._format_input_definition(input_def, label="per-user behavioral")
            for input_def in component.behavioral_inputs
        ]
        config_lines = [
            self._format_input_definition(input_def, label="configuration")
            for key in sorted(component.config_input_keys)
            for input_def in [self._config_input_definition(key)]
            if input_def is not None
        ]
        sections = [
            f"### {component.component_id} ({component.name})",
            f"- component_id: {component.component_id}",
            f"- component_type: {component.component_type}",
            f"- status: {tag}",
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
        component: SharedComponentUsageContext,
    ) -> list[str]:
        if component.component_type == "database":
            return [
                "Storage model (required for database components):",
                "Provide storage_model.entities with per-entity row counts and KB per row.",
                f"Suggested entities for this app type: {', '.join(RDS_ENTITY_SUGGESTIONS[:6])}.",
            ]
        if component.component_type == "object_storage":
            return [
                "Storage model (required for object_storage components):",
                "Provide storage_model.categories with per-category object counts and KB per object.",
                f"Suggested categories: {', '.join(S3_CATEGORY_SUGGESTIONS[:6])}.",
            ]
        return []

    @staticmethod
    def _format_requirements(context: SharedUsageContext) -> list[str]:
        lines: list[str] = []
        for key, enabled in context.requirements.items():
            label = REQUIREMENT_LABELS.get(key, key.replace("_", " ").title())
            lines.append(f"- {label}: {'yes' if enabled else 'no'}")
        return lines

    @staticmethod
    def _stage_guidance(stage: str) -> str:
        if stage == "production":
            return PROMPT_STAGE_GUIDANCE_PRODUCTION
        return PROMPT_STAGE_GUIDANCE_MVP

    @staticmethod
    def _format_input_definition(
        input_def: UsageInputDefinition,
        *,
        label: str,
    ) -> str:
        constraints: list[str] = []
        if input_def.min_value is not None:
            constraints.append(f"min={input_def.min_value}")
        if input_def.max_value is not None:
            constraints.append(f"max={input_def.max_value}")
        if input_def.default_value is not None:
            constraints.append(f"default={input_def.default_value!r}")
        constraint_text = f" ({', '.join(constraints)})" if constraints else ""
        return (
            f"- {input_def.key} [{label}]: {input_def.description} "
            f"Unit: {input_def.unit or 'n/a'}{constraint_text}"
        )

    @staticmethod
    def _config_input_definition(key: str) -> UsageInputDefinition | None:
        from app.pricing.schemas import InputDataType, UsageInputDefinition

        common: dict[str, UsageInputDefinition] = {
            "instance_hours_per_month": UsageInputDefinition(
                key="instance_hours_per_month",
                description="Provisioned compute hours per month.",
                unit="hours/month",
                data_type=InputDataType.float,
                default_value=730,
            ),
            "build_minutes_per_month": UsageInputDefinition(
                key="build_minutes_per_month",
                description="CI/build minutes consumed per month.",
                unit="minutes/month",
                data_type=InputDataType.float,
                default_value=30,
            ),
            "sku_tier": UsageInputDefinition(
                key="sku_tier",
                description="API gateway pricing tier.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Consumption",
            ),
            "api_type": UsageInputDefinition(
                key="api_type",
                description="API gateway protocol type.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="HTTP",
            ),
            "namespace_hours_per_month": UsageInputDefinition(
                key="namespace_hours_per_month",
                description="Notification namespace hours provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                default_value=730,
            ),
            "custom_metrics_count": UsageInputDefinition(
                key="custom_metrics_count",
                description="Custom metrics published.",
                unit="metrics",
                data_type=InputDataType.integer,
                default_value=5,
            ),
            "alert_rules_count": UsageInputDefinition(
                key="alert_rules_count",
                description="Alert rules configured.",
                unit="rules",
                data_type=InputDataType.integer,
                default_value=1,
            ),
            "alert_policies_count": UsageInputDefinition(
                key="alert_policies_count",
                description="Alert policies configured.",
                unit="policies",
                data_type=InputDataType.integer,
                default_value=1,
            ),
            "configuration_stores": UsageInputDefinition(
                key="configuration_stores",
                description="Configuration stores provisioned.",
                unit="stores",
                data_type=InputDataType.integer,
                default_value=1,
            ),
            "configurations_count": UsageInputDefinition(
                key="configurations_count",
                description="Configuration profiles provisioned.",
                unit="configurations",
                data_type=InputDataType.integer,
                default_value=2,
            ),
            "secrets_count": UsageInputDefinition(
                key="secrets_count",
                description="Secrets stored.",
                unit="secrets",
                data_type=InputDataType.integer,
                default_value=3,
            ),
            "deployment_events_per_month": UsageInputDefinition(
                key="deployment_events_per_month",
                description="Configuration deployment events per month.",
                unit="events/month",
                data_type=InputDataType.integer,
                default_value=4,
            ),
            "plan": UsageInputDefinition(
                key="plan",
                description="Serverless/compute plan.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="consumption",
            ),
            "avg_execution_duration_ms": UsageInputDefinition(
                key="avg_execution_duration_ms",
                description="Average execution duration.",
                unit="milliseconds",
                data_type=InputDataType.integer,
                default_value=200,
            ),
            "memory_mb": UsageInputDefinition(
                key="memory_mb",
                description="Allocated memory.",
                unit="MB",
                data_type=InputDataType.integer,
                default_value=512,
            ),
            "access_tier": UsageInputDefinition(
                key="access_tier",
                description="Blob/object storage access tier.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Hot",
            ),
            "redundancy": UsageInputDefinition(
                key="redundancy",
                description="Storage redundancy option.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="LRS",
            ),
            "list_operations": UsageInputDefinition(
                key="list_operations",
                description="Monthly list operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                default_value=1000,
            ),
            "static_storage_gb": UsageInputDefinition(
                key="static_storage_gb",
                description="Static storage not scaled by users.",
                unit="GB",
                data_type=InputDataType.float,
                default_value=0,
            ),
        }
        return common.get(key)
