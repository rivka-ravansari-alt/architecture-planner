"""Helpers for converting UsageContext to legacy inference inputs."""

from __future__ import annotations

from app.models import Project
from app.pricing.usage.schemas import CloudProvider, UsageContext
from app.schemas.domain import MappedComponent


def project_from_context(context: UsageContext) -> Project:
    return Project(
        name=context.product_name,
        description=context.description,
        expected_users=context.expected_users_label,
        stage=context.stage,
        architecture_summary=context.architecture_summary,
    )


def components_from_context(context: UsageContext) -> list[MappedComponent]:
    components: list[MappedComponent] = []
    for item in context.components:
        cloud: dict[str, str | None] = {"aws": None, "gcp": None, "azure": None}
        cloud[item.cloud.provider] = item.cloud.mapped_service_name
        components.append(
            MappedComponent(
                key=item.component_id,
                name=item.name,
                component_type=item.component_type,
                reason=item.reason,
                category="core",
                optional=item.optional,
                order=item.order,
                cloud=cloud,
            )
        )
    return components


def provider_cloud_key(provider: CloudProvider) -> str:
    return provider
