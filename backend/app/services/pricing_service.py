"""Application-level orchestration for Step 4 (progressive cloud pricing)."""

from __future__ import annotations

import logging
from typing import Any

from google.cloud import firestore

from app.config.params import (
    CLOUD_PROVIDER_LABELS,
    ERR_INVALID_CLOUD_PROVIDER,
    ERR_NO_COMPONENT_SELECTION,
    ERR_NO_GLOBAL_USAGE_MODEL,
    ERR_NO_PRICING_RUN,
    ERR_PRICING_RUN_NOT_FOUND,
    ERR_PROJECT_FORBIDDEN,
    ERR_PROJECT_NOT_FOUND,
    PRICING_GENERATION_ORDER,
)
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.repositories.cloud_service_mapping_repository import (
    CloudServiceMappingRepository,
)
from app.repositories.pricing_service_repository import PricingServiceRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.auth import UserOut
from app.schemas.global_usage_model import (
    GlobalUsageModelPayload,
    UsageParameterEstimate,
    coerce_static_usage_value,
)
from app.schemas.pricing import (
    PricingLineItem,
    PricingRunResponse,
    ProviderPricingResponse,
    ProviderPricingResult,
)
from app.services.component_pricing_resolver import resolve_service_for_component
from app.services.pricing_calculation_executor import (
    PricingCalculationError,
    execute_pricing_script,
)
from app.services.pricing_utils import format_service_type, pricing_service_display_name
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_inputs_builder import build_usage_inputs
from app.services.usage_parameter_resolver import UsageParameterResolver
from app.validators.usage_inputs_validator import validate_service_inputs

logger = logging.getLogger(__name__)


class PricingService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        mapping_repository: CloudServiceMappingRepository,
        pricing_repository: PricingServiceRepository,
        usage_parameter_resolver: UsageParameterResolver | None = None,
        static_value_resolver: StaticUsageValueResolver | None = None,
    ) -> None:
        self._projects = project_repository
        self._mappings = mapping_repository
        self._pricing = pricing_repository
        self._parameter_resolver = usage_parameter_resolver or UsageParameterResolver(
            mapping_repository,
            pricing_repository,
        )
        self._static_values = static_value_resolver or StaticUsageValueResolver()

    def generate_provider(
        self,
        project_id: str,
        provider: str,
        user: UserOut,
        *,
        run_id: str | None = None,
    ) -> ProviderPricingResponse:
        normalized_provider = provider.strip().lower()
        if normalized_provider not in PRICING_GENERATION_ORDER:
            raise BadRequestError(ERR_INVALID_CLOUD_PROVIDER)

        self._load_owned_project(project_id, user)
        selection, usage_model, usage_payload, usage_inputs = self._load_pricing_inputs(
            project_id
        )

        if run_id:
            run = self._projects.get_pricing_run(project_id, run_id)
            if run is None:
                raise NotFoundError(ERR_PRICING_RUN_NOT_FOUND)
            if not self._is_pricing_run_current(
                run,
                selection_id=selection["id"],
                usage_model_id=usage_model["id"],
            ):
                run_id = None

        if not run_id:
            run_id = self._projects.create_pricing_run(
                project_id,
                {
                    "selection_id": selection["id"],
                    "usage_model_id": usage_model["id"],
                    "status": "in_progress",
                    "stale": False,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
            )

        try:
            line_items = self._price_components_for_provider(
                selected=selection.get("selected", []),
                provider=normalized_provider,
                usage_inputs=usage_inputs,
            )
            monthly_total = round(
                sum(
                    item.monthly_price
                    for item in line_items
                    if item.status == "priced" and item.monthly_price is not None
                ),
                2,
            )
            result = ProviderPricingResult(
                provider=normalized_provider,
                provider_label=CLOUD_PROVIDER_LABELS[normalized_provider],
                status="completed",
                line_items=line_items,
                monthly_total=monthly_total,
            )
        except Exception as error:
            logger.exception(
                "provider pricing failed project_id=%s provider=%s",
                project_id,
                normalized_provider,
            )
            result = ProviderPricingResult(
                provider=normalized_provider,
                provider_label=CLOUD_PROVIDER_LABELS[normalized_provider],
                status="failed",
                error=str(error),
            )

        try:
            self._projects.save_provider_pricing_result(
                project_id,
                run_id,
                normalized_provider,
                {
                    "provider": normalized_provider,
                    "status": result.status,
                    "line_items": [
                        item.model_dump(mode="json") for item in result.line_items
                    ],
                    "monthly_total": result.monthly_total,
                    "error": result.error,
                    "created_at": firestore.SERVER_TIMESTAMP,
                },
            )
        except Exception as error:
            logger.exception(
                "failed to persist provider pricing project_id=%s run_id=%s provider=%s",
                project_id,
                run_id,
                normalized_provider,
            )
            if result.error:
                result = result.model_copy(
                    update={
                        "error": f"{result.error}; also failed to save: {error}",
                    }
                )
            else:
                result = result.model_copy(
                    update={"error": f"Pricing calculated but failed to save: {error}"}
                )

        provider_results = self._projects.list_provider_pricing_results(
            project_id, run_id
        )
        if len(provider_results) >= len(PRICING_GENERATION_ORDER):
            self._projects.update_pricing_run(
                project_id,
                run_id,
                {"status": "completed", "updated_at": firestore.SERVER_TIMESTAMP},
            )
            self._projects.set_current_step(project_id, 4)

        logger.info(
            "saved provider pricing project_id=%s run_id=%s provider=%s status=%s total=%.2f",
            project_id,
            run_id,
            normalized_provider,
            result.status,
            result.monthly_total,
        )

        return ProviderPricingResponse(
            run_id=run_id,
            selection_id=selection["id"],
            usage_model_id=usage_model["id"],
            result=result,
        )

    def get_latest_pricing(self, project_id: str, user: UserOut) -> PricingRunResponse:
        self._load_owned_project(project_id, user)
        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)

        run = self._projects.get_latest_pricing_run(project_id)
        if run is None:
            raise NotFoundError(ERR_NO_PRICING_RUN)

        usage_model = self._projects.get_latest_global_usage_model(project_id)
        if not self._is_pricing_run_current(
            run,
            selection_id=selection["id"],
            usage_model_id=usage_model["id"] if usage_model else "",
        ):
            raise NotFoundError(ERR_NO_PRICING_RUN)

        provider_results = self._projects.list_provider_pricing_results(
            project_id, run["id"]
        )
        return PricingRunResponse.from_stored_run(run, provider_results)

    def get_pricing_run(
        self, project_id: str, run_id: str, user: UserOut
    ) -> PricingRunResponse:
        self._load_owned_project(project_id, user)
        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)

        run = self._projects.get_pricing_run(project_id, run_id)
        if run is None:
            raise NotFoundError(ERR_PRICING_RUN_NOT_FOUND)

        usage_model = self._projects.get_latest_global_usage_model(project_id)
        if not self._is_pricing_run_current(
            run,
            selection_id=selection["id"],
            usage_model_id=usage_model["id"] if usage_model else "",
        ):
            raise NotFoundError(ERR_PRICING_RUN_NOT_FOUND)

        provider_results = self._projects.list_provider_pricing_results(
            project_id, run_id
        )
        return PricingRunResponse.from_stored_run(run, provider_results)

    def _load_owned_project(self, project_id: str, user: UserOut) -> dict[str, Any]:
        project = self._projects.find_by_id(project_id)
        if project is None:
            raise NotFoundError(ERR_PROJECT_NOT_FOUND)
        if project.get("user_id") != user.id:
            raise ForbiddenError(ERR_PROJECT_FORBIDDEN)
        return project

    def _load_pricing_inputs(
        self, project_id: str
    ) -> tuple[dict[str, Any], dict[str, Any], GlobalUsageModelPayload, dict[str, Any]]:
        project = self._projects.find_by_id(project_id)
        if project is None:
            raise NotFoundError(ERR_PROJECT_NOT_FOUND)

        selection = self._projects.get_latest_architecture_selection(project_id)
        if selection is None:
            raise NotFoundError(ERR_NO_COMPONENT_SELECTION)

        usage_model = self._projects.get_latest_global_usage_model(project_id)
        if usage_model is None or usage_model.get("stale"):
            raise NotFoundError(ERR_NO_GLOBAL_USAGE_MODEL)
        if usage_model.get("selection_id") != selection["id"]:
            raise NotFoundError(ERR_NO_GLOBAL_USAGE_MODEL)

        usage_payload = self._usage_payload_from_document(usage_model)
        usage_payload = self._refresh_static_usage_values(
            usage_payload,
            project=project,
            selected=selection.get("selected", []),
        )
        usage_inputs = build_usage_inputs(usage_payload)
        return selection, usage_model, usage_payload, usage_inputs

    def _refresh_static_usage_values(
        self,
        payload: GlobalUsageModelPayload,
        *,
        project: dict[str, Any],
        selected: list[dict[str, Any]],
    ) -> GlobalUsageModelPayload:
        """Re-resolve project-backed static inputs at pricing time.

        Saved Step 3 models can lag behind pricing-service ``to_know.static``
        changes (e.g. ``authentication_methods``). Static values always come
        from the current project intake, so refresh them before pricing.
        """

        resolved = self._parameter_resolver.resolve_for_selected_components(selected)
        if not resolved.static:
            return payload

        fresh_static = self._static_values.resolve(
            resolved.static,
            expected_users=int(project.get("expected_users", 0) or 0),
            stage=str(project.get("stage") or ""),
            requirements=project.get("requirements") or {},
        )
        return GlobalUsageModelPayload(
            llm=payload.llm,
            static={**payload.static, **fresh_static},
        )

    @staticmethod
    def _is_pricing_run_current(
        run: dict[str, Any],
        *,
        selection_id: str,
        usage_model_id: str,
    ) -> bool:
        if run.get("stale"):
            return False
        if run.get("selection_id") != selection_id:
            return False
        if not usage_model_id or run.get("usage_model_id") != usage_model_id:
            return False
        return True

    @staticmethod
    def _usage_payload_from_document(document: dict[str, Any]) -> GlobalUsageModelPayload:
        usage_model = document.get("usage_model") or {}
        llm_payload = usage_model.get("llm") or document.get("usage") or {}
        static_payload = usage_model.get("static") or document.get("static") or {}

        llm = {
            parameter: UsageParameterEstimate.model_validate(estimate)
            for parameter, estimate in llm_payload.items()
        }
        static: dict[str, str | int | float | list[str]] = {}
        for parameter, value in static_payload.items():
            coerced = coerce_static_usage_value(value)
            if coerced is not None:
                static[parameter] = coerced

        return GlobalUsageModelPayload(llm=llm, static=static)

    def _price_components_for_provider(
        self,
        *,
        selected: list[dict[str, Any]],
        provider: str,
        usage_inputs: dict[str, Any],
    ) -> list[PricingLineItem]:
        if not selected:
            raise PricingCalculationError(
                f"No selected components are available to price for {provider}."
            )

        line_items: list[PricingLineItem] = []

        for component in selected:
            instance_id = component.get("instance_id") or component.get("uid")
            category_id = component.get("category_id") or component.get("id")
            component_name = component.get("name") or category_id or "Unknown component"
            selection_reason = self._selection_reason_from_component(component)

            if not instance_id or not category_id:
                line_items.append(
                    PricingLineItem(
                        instance_id=instance_id or "missing-instance",
                        category_id=category_id or "missing-category",
                        component_name=component_name,
                        status="skipped",
                        skip_reason=(
                            "Component is missing instance_id or category_id in the "
                            "saved selection."
                        ),
                        selection_reason=selection_reason,
                    )
                )
                continue

            resolution = resolve_service_for_component(
                mapping_repository=self._mappings,
                pricing_repository=self._pricing,
                category_id=category_id,
                provider=provider,
            )
            if resolution.service_entry is None:
                line_items.append(
                    PricingLineItem(
                        instance_id=instance_id,
                        category_id=category_id,
                        component_name=component_name,
                        status="skipped",
                        skip_reason=resolution.skip_reason,
                        selection_reason=selection_reason,
                    )
                )
                continue

            service_id = resolution.service_entry["service_id"]
            pricing_service = self._pricing.find_by_id(service_id)
            if pricing_service is None:
                line_items.append(
                    PricingLineItem(
                        instance_id=instance_id,
                        category_id=category_id,
                        component_name=component_name,
                        status="skipped",
                        skip_reason=(
                            f"Pricing definition for '{service_id}' was not found."
                        ),
                        selection_reason=selection_reason,
                    )
                )
                continue

            script = pricing_service.get("script_calculation", "")
            if not script or not script.strip():
                line_items.append(
                    PricingLineItem(
                        instance_id=instance_id,
                        category_id=category_id,
                        component_name=component_name,
                        service_id=service_id,
                        service_name=pricing_service_display_name(service_id),
                        service_type=format_service_type(
                            resolution.service_entry.get("service_type")
                        ),
                        status="skipped",
                        skip_reason=(
                            f"Pricing definition for '{service_id}' has no "
                            f"calculation script."
                        ),
                        selection_reason=selection_reason,
                    )
                )
                continue

            skus = pricing_service.get("skus") or []
            free_tier = pricing_service.get("free_tier") or {}
            if not isinstance(skus, list):
                skus = []
            if not isinstance(free_tier, dict):
                free_tier = {}

            to_know = pricing_service.get("to_know")
            if not isinstance(to_know, dict):
                to_know = None

            try:
                validate_service_inputs(service_id, usage_inputs)
                script_result = execute_pricing_script(
                    script,
                    inputs=usage_inputs,
                    skus=skus,
                    free_tier=free_tier,
                    to_know=to_know,
                    service_id=service_id,
                )
            except PricingCalculationError as error:
                line_items.append(
                    PricingLineItem(
                        instance_id=instance_id,
                        category_id=category_id,
                        component_name=component_name,
                        service_id=service_id,
                        service_name=pricing_service_display_name(service_id),
                        service_type=format_service_type(
                            resolution.service_entry.get("service_type")
                        ),
                        status="failed",
                        skip_reason=str(error),
                        selection_reason=selection_reason,
                    )
                )
                continue

            line_items.append(
                PricingLineItem(
                    instance_id=instance_id,
                    category_id=category_id,
                    component_name=component_name,
                    service_id=service_id,
                    service_name=pricing_service_display_name(service_id),
                    service_type=format_service_type(
                        resolution.service_entry.get("service_type")
                    ),
                    monthly_price=script_result.monthly_price,
                    status="priced",
                    selection_reason=selection_reason,
                    calculation_summary=script_result.calculation_summary,
                    details=script_result.details,
                )
            )

        return line_items

    @staticmethod
    def _selection_reason_from_component(component: dict[str, Any]) -> str | None:
        """Return the Step 2 selection reason for this instance, if saved."""

        reason = component.get("reason")
        if not isinstance(reason, str):
            return None
        cleaned = reason.strip()
        return cleaned or None

    def _resolve_service_for_component(
        self,
        *,
        category_id: str,
        provider: str,
    ) -> dict[str, Any] | None:
        resolution = resolve_service_for_component(
            mapping_repository=self._mappings,
            pricing_repository=self._pricing,
            category_id=category_id,
            provider=provider,
        )
        return resolution.service_entry
