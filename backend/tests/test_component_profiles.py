"""Tests for component pricing profiles and SKU classification."""

from __future__ import annotations

from app.services.pricing.component_profiles import (
    FormulaKind,
    PricingRole,
    PROFILE_CLOUD_RUN,
    PROFILE_DATABASE_SQL,
    PROFILE_LAMBDA,
    PROFILE_OBJECT_STORAGE,
    PROFILE_WEB_APP,
    iter_default_profile_documents,
    resolve_component_profile,
    resolve_component_profile_with_source,
)
from app.services.pricing.pricing_profile_repository import PricingProfileRepository
from app.services.pricing.profile_engine import build_plan_from_profile, optional_role_applies
from app.services.pricing.sku_classifier import classify_sku, evaluate_sku_for_role, iter_skus_for_role
from app.config.params import FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import RequirementContext


def test_cloud_run_profile_roles_and_formula():
    profile = resolve_component_profile("app_service", "Cloud Run")
    assert profile.name == "cloud_run"
    assert profile.formula == FormulaKind.CLOUD_RUN
    assert profile.is_required(PricingRole.CPU)
    assert profile.is_required(PricingRole.MEMORY)
    assert profile.is_required(PricingRole.REQUESTS)
    assert profile.allows(PricingRole.EGRESS)
    assert not profile.allows(PricingRole.GATEWAY_CAPACITY)


def test_lambda_profile_roles():
    profile = resolve_component_profile("app_service", "Lambda")
    assert profile.formula == FormulaKind.LAMBDA
    assert profile.is_required(PricingRole.REQUESTS)
    assert profile.is_required(PricingRole.GB_SECONDS)
    assert not profile.is_required(PricingRole.CPU)


def test_api_gateway_profile_requests_only():
    profile = resolve_component_profile("api_gateway", "API Gateway")
    assert profile.formula == FormulaKind.REQUESTS_ONLY
    assert profile.required_roles == frozenset({PricingRole.REQUESTS})


def test_object_storage_profile():
    assert PROFILE_OBJECT_STORAGE.formula == FormulaKind.OBJECT_STORAGE
    assert profile_is_required(PROFILE_OBJECT_STORAGE, PricingRole.STORAGE)
    assert profile_is_required(PROFILE_OBJECT_STORAGE, PricingRole.READ_OPERATIONS)
    assert profile_is_required(PROFILE_OBJECT_STORAGE, PricingRole.WRITE_OPERATIONS)


def test_auth_mutually_exclusive():
    profile = resolve_component_profile("auth", "Cognito")
    group = profile.exclusive_group_for(PricingRole.MAU)
    assert group is not None
    assert PricingRole.AUTH_EVENTS in group


def profile_is_required(profile, role: PricingRole) -> bool:
    return profile.is_required(role)


def test_classify_rejects_networking_for_memory():
    role = classify_sku(
        "egress_ondemand",
        {"description": "Cloud Run Network Internet Egress", "usage_unit": "GiBy", "unit_price_usd": 0.19},
    )
    assert role in {PricingRole.EGRESS, PricingRole.DATA_TRANSFER}
    assert role != PricingRole.MEMORY


def test_classify_rejects_front_door_for_hosting():
    role = classify_sku(
        "standard",
        {"description": "Standard Azure Front Door Add-on", "usage_unit": "1 Hour", "unit_price_usd": 0.024},
    )
    assert role not in {PricingRole.HOSTING, PricingRole.COMPUTE, PricingRole.REQUESTS}


def test_iter_skus_respects_profile_roles():
    skus = {
        "cpu": {"description": "Cloud Run CPU", "usage_unit": "vcpu.s", "unit_price_usd": 0.00001},
        "egress": {"description": "Network egress", "usage_unit": "GiBy", "unit_price_usd": 0.12},
    }
    assert len(iter_skus_for_role(skus, PROFILE_CLOUD_RUN, PricingRole.CPU)) == 1
    assert len(iter_skus_for_role(skus, PROFILE_LAMBDA, PricingRole.EGRESS)) == 1
    assert len(iter_skus_for_role(skus, PROFILE_LAMBDA, PricingRole.CPU)) == 0


def test_database_profile_rejects_export_skus():
    skus = {
        "export": {
            "description": "RDS snapshot export to S3",
            "usage_unit": "GiBy",
            "unit_price_usd": 0.10,
            "sku_id": "export-1",
        },
        "storage": {
            "description": "RDS storage",
            "usage_unit": "GiBy.mo",
            "unit_price_usd": 0.115,
            "sku_id": "storage-1",
        },
    }
    assert len(iter_skus_for_role(skus, PROFILE_DATABASE_SQL, PricingRole.STORAGE)) == 1
    reject_log: list[dict[str, str]] = []
    iter_skus_for_role(skus, PROFILE_DATABASE_SQL, PricingRole.STORAGE, reject_log=reject_log)
    assert any("export" in item["catalog_role"] for item in reject_log)


def test_storage_profile_rejects_cdn_skus():
    skus = {
        "cdn": {
            "description": "S3 CDN cache-fill",
            "usage_unit": "GiBy",
            "unit_price_usd": 0.02,
            "sku_id": "cdn-1",
        },
        "storage": {
            "description": "S3 standard storage",
            "usage_unit": "GiBy.mo",
            "unit_price_usd": 0.023,
            "sku_id": "storage-1",
        },
    }
    assert len(iter_skus_for_role(skus, PROFILE_OBJECT_STORAGE, PricingRole.STORAGE)) == 1


def test_web_app_rejects_front_door_skus():
    ok, reason = evaluate_sku_for_role(
        "addon",
        {"description": "Azure Front Door Add-on", "usage_unit": "1 Hour", "unit_price_usd": 0.024},
        PROFILE_WEB_APP,
        PricingRole.HOSTING,
    )
    assert not ok
    assert reason is not None


def test_cloud_run_memory_rejects_network_skus():
    ok, reason = evaluate_sku_for_role(
        "memory",
        {"description": "Cloud Run memory network egress", "usage_unit": "GiBy", "unit_price_usd": 0.12},
        PROFILE_CLOUD_RUN,
        PricingRole.MEMORY,
    )
    assert not ok


def test_optional_egress_skipped_without_file_upload():
    requirements = RequirementContext(file_upload=False, ai=False)
    assert not optional_role_applies(
        PricingRole.EGRESS,
        PROFILE_CLOUD_RUN,
        stage="mvp",
        expected_users="1000",
        requirements=requirements,
    )


def test_build_plan_includes_audit():
    from app.services.pricing.usage_profile import UsageProfile

    skus = {
        "cpu": {"description": "Cloud Run CPU", "usage_unit": "vcpu.s", "unit_price_usd": 0.000024},
        "memory": {"description": "Cloud Run Memory", "usage_unit": "gib.s", "unit_price_usd": 0.0000025},
        "requests": {"description": "Cloud Run requests", "usage_unit": "1M", "unit_price_usd": 0.40},
    }
    usage = UsageProfile(
        values={"monthly_vcpu_hours": 100, "monthly_memory_gib_hours": 200, "monthly_requests": 1_000_000},
        assumptions={"user_count": 1000, "stage": "mvp"},
        missing_defaults=[],
    )
    plan = build_plan_from_profile(
        comp_profile=PROFILE_CLOUD_RUN,
        skus=skus,
        usage=usage,
        stage="mvp",
        expected_users="1000",
        requirements=RequirementContext(),
    )
    assert plan.audit is not None
    assert plan.audit.profile_name == "cloud_run"
    assert len(plan.audit.selected) >= 2
    assert plan.audit.formula_expression


def test_repository_loads_firestore_profile_by_provider_component_service():
    client = FakeFirestoreClient()
    for doc in iter_default_profile_documents():
        client.collection(FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES).document(doc["id"]).set(doc)

    repository = PricingProfileRepository(client)
    profile = repository.get_profile(
        provider="gcp",
        component_type="app_service",
        cloud_service="Cloud Run",
    )

    assert profile is not None
    assert profile.name == "cloud_run"
    assert profile.formula == FormulaKind.CLOUD_RUN


def test_resolve_missing_firestore_profile_does_not_fallback_by_default():
    client = FakeFirestoreClient()
    repository = PricingProfileRepository(client)

    resolution = resolve_component_profile_with_source(
        "app_service",
        "Cloud Run",
        provider="gcp",
        repository=repository,
    )

    assert resolution.profile is None
    assert resolution.missing_data == ["missing_pricing_profile"]
    assert not resolution.used_fallback
