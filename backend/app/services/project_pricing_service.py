"""Top-level project pricing facade for generate_pricing."""

from __future__ import annotations

from app.config.params import CLOUD_PROVIDERS, COST_CURRENCY
from app.models import Project
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.azure.project_costing import AzureProjectCostingPipeline
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.providers.heuristic import HeuristicProviderPricing
from app.pricing.schemas import ComponentPricingInput
from app.schemas.domain import MappedComponent, ProviderCost
from app.services.component_mapper_service import ComponentMapperService


class ProjectPricingService:
    """Estimate project costs from Azure, AWS, and GCP catalog pipelines."""

    def __init__(
        self,
        azure_pipeline: AzureProjectCostingPipeline,
        aws_pipeline: AwsProjectCostingPipeline,
        gcp_pipeline: GcpProjectCostingPipeline,
        heuristic_pricing: HeuristicProviderPricing,
    ) -> None:
        self._azure_pipeline = azure_pipeline
        self._aws_pipeline = aws_pipeline
        self._gcp_pipeline = gcp_pipeline
        self._heuristic_pricing = heuristic_pricing

    @classmethod
    def create_default(cls, mapper: ComponentMapperService) -> ProjectPricingService:
        """Build a service with Firestore-backed catalog lookup for all providers."""
        from app.pricing.catalog_factory import build_project_pricing_service

        return build_project_pricing_service(mapper)

    def estimate(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        mapper: ComponentMapperService | None = None,
        pricing_inputs: list[ComponentPricingInput] | None = None,
        aws_pricing_inputs: list[ComponentPricingInput] | None = None,
        gcp_pricing_inputs: list[ComponentPricingInput] | None = None,
        inference_source: str | None = None,
        aws_inference_source: str | None = None,
        gcp_inference_source: str | None = None,
    ) -> list[ProviderCost]:
        """Return monthly cost estimates for all configured cloud providers."""
        active_mapper = mapper or self._heuristic_pricing._mapper
        feature_flags = (
            active_mapper.feature_flags_from_components(components)
            if active_mapper is not None
            else {}
        )
        azure_result = self._azure_pipeline.calculate(
            project,
            components,
            feature_flags=feature_flags,
            pricing_inputs=pricing_inputs,
        )
        azure_total = round(azure_result.total_usd, 2)
        azure_detail = azure_result.model_dump(mode="json")
        if inference_source is not None:
            azure_detail["inference_source"] = inference_source

        aws_result = self._aws_pipeline.calculate(
            project,
            components,
            feature_flags=feature_flags,
            pricing_inputs=aws_pricing_inputs,
        )
        aws_total = round(aws_result.total_usd, 2)
        aws_detail = aws_result.model_dump(mode="json")
        aws_source = aws_inference_source or inference_source
        if aws_source is not None:
            aws_detail["inference_source"] = aws_source

        gcp_result = self._gcp_pipeline.calculate(
            project,
            components,
            feature_flags=feature_flags,
            pricing_inputs=gcp_pricing_inputs,
        )
        gcp_total = round(gcp_result.total_usd, 2)
        gcp_detail = gcp_result.model_dump(mode="json")
        gcp_source = gcp_inference_source or inference_source
        if gcp_source is not None:
            gcp_detail["inference_source"] = gcp_source

        priced_lines = sum(len(c.line_items) for c in azure_result.components)
        warning_count = len(azure_result.warnings) + len(azure_result.missing_prices)
        source_label = {
            "llm": "LLM-inferred usage",
            "heuristic_fallback": "heuristic fallback usage",
            "heuristic_only": "heuristic usage",
        }.get(inference_source or "", "catalog pricing")
        azure_notes = (
            f"Catalog-based Azure estimate at ~{project.expected_users} users "
            f"({project.stage}) using {source_label}. {priced_lines} priced SKU line(s)."
        )
        if warning_count:
            azure_notes += f" {warning_count} pricing warning(s)."

        aws_priced_lines = sum(len(c.line_items) for c in aws_result.components)
        aws_warning_count = len(aws_result.warnings) + len(aws_result.missing_prices)
        aws_unsupported = aws_result.unsupported_component_count
        aws_source_label = {
            "llm": "LLM-inferred usage",
            "heuristic_fallback": "heuristic fallback usage",
            "heuristic_only": "heuristic usage",
        }.get(aws_source or "", "catalog pricing")
        aws_notes = (
            f"Catalog-based AWS estimate at ~{project.expected_users} users "
            f"({project.stage}) using {aws_source_label}. {aws_priced_lines} priced SKU line(s)."
        )
        if aws_warning_count:
            aws_notes += f" {aws_warning_count} pricing warning(s)."
        if aws_unsupported:
            aws_notes += f" {aws_unsupported} unsupported AWS component(s) explicitly marked."

        gcp_priced_lines = sum(len(c.line_items) for c in gcp_result.components)
        gcp_warning_count = len(gcp_result.warnings) + len(gcp_result.missing_prices)
        gcp_unsupported = gcp_result.unsupported_component_count
        gcp_ui_only = gcp_result.ui_only_component_count
        gcp_source_label = {
            "llm": "LLM-inferred usage",
            "heuristic_fallback": "heuristic fallback usage",
            "heuristic_only": "heuristic usage",
        }.get(gcp_source or "", "catalog pricing")
        gcp_notes = (
            f"Catalog-based GCP estimate at ~{project.expected_users} users "
            f"({project.stage}) using {gcp_source_label}. {gcp_priced_lines} priced SKU line(s)."
        )
        if gcp_warning_count:
            gcp_notes += f" {gcp_warning_count} pricing warning(s)."
        if gcp_unsupported:
            gcp_notes += f" {gcp_unsupported} unsupported GCP component(s) explicitly marked."
        if gcp_ui_only:
            gcp_notes += (
                f" {gcp_ui_only} UI-only GCP component(s) at $0 "
                "(costs via backing services, e.g. BigQuery for Looker Studio)."
            )

        return [
            ProviderCost(
                provider="azure",
                monthly_low=azure_total,
                monthly_high=azure_total,
                currency=COST_CURRENCY,
                notes=azure_notes,
                pricing_detail=azure_detail,
            ),
            ProviderCost(
                provider="aws",
                monthly_low=aws_total,
                monthly_high=aws_total,
                currency=COST_CURRENCY,
                notes=aws_notes,
                pricing_detail=aws_detail,
            ),
            ProviderCost(
                provider="gcp",
                monthly_low=gcp_total,
                monthly_high=gcp_total,
                currency=COST_CURRENCY,
                notes=gcp_notes,
                pricing_detail=gcp_detail,
            ),
        ]
