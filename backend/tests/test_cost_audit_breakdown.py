"""Unit tests for cost audit breakdown and known calculation scenarios."""

from __future__ import annotations

import pytest

from app.config.params import (
    FIRESTORE_COLLECTION_GCP_CATALOG,
    FIRESTORE_COLLECTION_GCP_PRICING_PROFILES,
    PRICING_MODEL_COMPUTE_REQUEST,
    PRICING_MODEL_DATABASE_REQUEST,
    PRICING_MODEL_STORAGE,
    PRICING_MODEL_TOKEN,
)
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.audit_validator import validate_component_audit
from app.services.cost_calculation.calculators.profile_driven import ProfileDrivenCalculator
from app.services.cost_calculation.models import (
    CalculationContext,
    ComponentCostAudit,
    PricingCatalogRecord,
    SkuLineItem,
)
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.data.pricing_profiles_seed import build_pricing_profile_doc
from app.services.usage_estimation import ProductCapabilities, UsageEstimator


def _context(usage: dict[str, float], expected_users: str = "100") -> CalculationContext:
    return CalculationContext(
        provider="gcp",
        expected_users=expected_users,
        stage="mvp",
        usage=usage,
    )


def _usage_for_100_users() -> dict[str, float]:
    estimate = UsageEstimator().estimate(
        expected_users="100",
        stage="mvp",
        components=[],
        capabilities=ProductCapabilities(ai=True),
    )
    return estimate.global_consumption.to_pricing_metrics()


def _cloud_run_record() -> PricingCatalogRecord:
    return PricingCatalogRecord(
        id="cloud-run",
        name="Cloud Run",
        provider="gcp",
        skus={
            "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
            "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
            "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
        },
        formula={
            "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
            "request_cost": "(monthly_requests / 1000000) * skus.requests.unit_price_usd",
            "total": "cpu_cost + request_cost",
        },
    )


def _firestore_record() -> PricingCatalogRecord:
    return PricingCatalogRecord(
        id="firestore",
        name="Firestore",
        provider="gcp",
        skus={
            "reads": {"sku_id": "fs-read", "unit_price_usd": 0.06, "usage_unit": "1M reads"},
            "writes": {"sku_id": "fs-write", "unit_price_usd": 0.18, "usage_unit": "1M writes"},
            "storage": {"sku_id": "fs-storage", "unit_price_usd": 0.18, "usage_unit": "GiBy.mo"},
        },
        formula="database_request_based",
    )


def _cloud_storage_record() -> PricingCatalogRecord:
    return PricingCatalogRecord(
        id="cloud-storage",
        name="Cloud Storage",
        provider="gcp",
        skus={
            "storage": {"sku_id": "gcs-storage", "unit_price_usd": 0.020, "usage_unit": "GiBy.mo"},
        },
        formula="storage_based",
    )


def _vertex_ai_record() -> PricingCatalogRecord:
    return PricingCatalogRecord(
        id="vertex-ai",
        name="Vertex AI",
        provider="gcp",
        skus={
            "input_tokens": {"sku_id": "vai-in", "unit_price_usd": 0.00025, "usage_unit": "1K input tokens"},
            "output_tokens": {"sku_id": "vai-out", "unit_price_usd": 0.0005, "usage_unit": "1K output tokens"},
        },
        formula="token_based",
    )


def _profile(service_name: str):
    return PricingProfileRepository(FakeFirestoreClient())._profile_from_doc(
        build_pricing_profile_doc("gcp", service_name),
        provider="gcp",
    )


def test_cloud_run_style_api_100_users():
    """Cloud Run: cpu + memory + per-1M requests for 100-user profile."""
    usage = _usage_for_100_users()
    record = _cloud_run_record()
    result = ProfileDrivenCalculator(_profile("Cloud Run")).calculate(record, _context(usage))

    assert result.pricing_model == PRICING_MODEL_COMPUTE_REQUEST
    assert len(result.sku_lines) == 3

    monthly_requests = usage["monthly_requests"]
    cpu_hours = usage["cpu_seconds"] / 3600
    memory_hours = usage["memory_gib_seconds"] / 3600
    req_qty = monthly_requests / 1_000_000

    expected_cpu = cpu_hours * 0.000024
    expected_mem = memory_hours * 0.0000025
    expected_req = req_qty * 0.40
    expected_total = expected_cpu + expected_mem + expected_req

    roles = {line.sku_role: line for line in result.sku_lines}
    assert roles["cpu"].calculated_quantity == pytest.approx(cpu_hours)
    assert roles["memory"].calculated_quantity == pytest.approx(memory_hours)
    assert roles["requests"].calculated_quantity == pytest.approx(req_qty)
    assert result.monthly_cost == pytest.approx(expected_total, rel=1e-6)


def test_firestore_read_write_storage():
    """Firestore: reads/writes per 1M + storage GB-month."""
    usage = _usage_for_100_users()
    record = _firestore_record()
    result = ProfileDrivenCalculator(_profile("Cloud Firestore")).calculate(record, _context(usage))

    assert result.pricing_model == PRICING_MODEL_DATABASE_REQUEST
    roles = {line.sku_role: line for line in result.sku_lines}

    database_reads = usage["database_reads"]
    database_writes = usage["database_writes"]
    storage_gb = usage["database_storage_gb"]
    expected_reads = (database_reads / 1_000_000) * 0.06
    expected_writes = (database_writes / 1_000_000) * 0.18
    expected_storage = storage_gb * 0.18
    expected_total = expected_reads + expected_writes + expected_storage

    assert roles["reads"].calculated_quantity == pytest.approx(database_reads / 1_000_000)
    assert roles["writes"].calculated_quantity == pytest.approx(database_writes / 1_000_000)
    assert roles["storage"].calculated_quantity == pytest.approx(storage_gb)
    assert result.monthly_cost == pytest.approx(expected_total, rel=1e-6)


def test_cloud_storage_gb_month():
    """Cloud Storage: storage_gb * unit_price."""
    usage = _usage_for_100_users()
    record = _cloud_storage_record()
    result = ProfileDrivenCalculator(_profile("Cloud Storage")).calculate(record, _context(usage))

    assert result.pricing_model == PRICING_MODEL_STORAGE
    storage_gb = usage["storage_gb"]
    expected = storage_gb * 0.020

    assert len(result.sku_lines) == 1
    assert result.sku_lines[0].sku_role == "storage"
    assert result.sku_lines[0].calculated_quantity == pytest.approx(storage_gb)
    assert result.monthly_cost == pytest.approx(expected)


def test_token_based_ai_pricing():
    """Vertex AI: input/output tokens per 1K."""
    usage = _usage_for_100_users()
    record = _vertex_ai_record()
    result = ProfileDrivenCalculator(_profile("Vertex AI")).calculate(record, _context(usage))

    assert result.pricing_model == PRICING_MODEL_TOKEN
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    input_qty = input_tokens / 1_000
    output_qty = output_tokens / 1_000
    expected = input_qty * 0.00025 + output_qty * 0.0005

    roles = {line.sku_role: line for line in result.sku_lines}
    assert roles["input_tokens"].calculated_quantity == pytest.approx(input_qty)
    assert roles["output_tokens"].calculated_quantity == pytest.approx(output_qty)
    assert result.monthly_cost == pytest.approx(expected, rel=1e-6)


def test_unit_mismatch_detects_per_million_error():
    audit = ComponentCostAudit(
        component_key="api",
        component_name="API",
        component_type="api",
        service_name="Bad API",
        pricing_record_id="bad",
        pricing_record_name="Bad API",
        pricing_model=PRICING_MODEL_COMPUTE_REQUEST,
        formula={},
        expected_users="100",
        usage_assumptions={"monthly_requests": 3000},
        sku_lines=[
            SkuLineItem(
                sku_role="requests",
                sku_id="bad-req",
                usage_unit="1M requests",
                unit_price=3.50,
                calculated_quantity=3000.0,
                quantity_note="monthly_requests (wrong)",
                line_item_cost=10500.0,
            )
        ],
        final_component_cost=10500.0,
        optional=False,
        pricing_profile_id="cloud-run",
        pricing_profile_service="Cloud Run",
        billable_sku_roles=["requests"],
    )
    warnings = validate_component_audit(audit)
    assert any("per-1M" in w for w in warnings)
    assert any("exceeds" in w or "suspiciously" in w for w in warnings)


def test_missing_required_sku_role_warns():
    audit = ComponentCostAudit(
        component_key="api",
        component_name="API",
        component_type="api",
        service_name="Cloud Run",
        pricing_record_id="cloud-run",
        pricing_record_name="Cloud Run",
        pricing_model=PRICING_MODEL_COMPUTE_REQUEST,
        formula={},
        expected_users="100",
        usage_assumptions={"monthly_requests": 3000},
        sku_lines=[
            SkuLineItem(
                sku_role="cpu",
                sku_id="cr-cpu",
                usage_unit="vcpu-hour",
                unit_price=0.000024,
                calculated_quantity=0.001,
                quantity_note="cpu",
                line_item_cost=0.000024,
            )
        ],
        final_component_cost=0.000024,
        optional=False,
        pricing_profile_id="cloud-run",
        pricing_profile_service="Cloud Run",
        billable_sku_roles=["cpu", "memory", "requests"],
    )
    warnings = validate_component_audit(audit)
    assert any("missing required SKU role 'memory'" in w for w in warnings)
    assert any("missing required SKU role 'requests'" in w for w in warnings)


def test_zero_api_cost_with_requests_warns():
    audit = ComponentCostAudit(
        component_key="api",
        component_name="API",
        component_type="api",
        service_name="Cloud Run",
        pricing_record_id="cloud-run",
        pricing_record_name="Cloud Run",
        pricing_model=PRICING_MODEL_COMPUTE_REQUEST,
        formula={},
        expected_users="100",
        usage_assumptions={"monthly_requests": 3000},
        sku_lines=[],
        final_component_cost=0.0,
        optional=False,
        pricing_profile_id="cloud-run",
        pricing_profile_service="Cloud Run",
        billable_sku_roles=["cpu", "memory", "requests"],
    )
    warnings = validate_component_audit(audit)
    assert any("$0 but monthly_requests" in w for w in warnings)


def _seed_audit_catalog(client: FakeFirestoreClient) -> None:
    docs = [
        {
            "id": "cloud-run",
            "name": "Cloud Run",
            "enabled": True,
            "skus": {
                "cpu": {"sku_id": "cr-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
                "memory": {"sku_id": "cr-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
                "requests": {"sku_id": "cr-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
            },
            "formula": {
                "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
                "request_cost": "(monthly_requests / 1000000) * skus.requests.unit_price_usd",
                "total": "cpu_cost + request_cost",
            },
        },
        {
            "id": "cloud-storage",
            "name": "Cloud Storage",
            "enabled": True,
            "skus": {
                "storage": {"sku_id": "gcs-storage", "unit_price_usd": 0.020, "usage_unit": "GiBy.mo"},
            },
            "formula": "storage_based",
        },
    ]
    for doc in docs:
        client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document(doc["id"]).set(doc)
    for service_name in ("Cloud Run", "Cloud Storage"):
        profile_doc = build_pricing_profile_doc("gcp", service_name)
        client.collection(FIRESTORE_COLLECTION_GCP_PRICING_PROFILES).document(profile_doc["id"]).set(profile_doc)


def test_end_to_end_breakdown_in_provider_cost():
    client = FakeFirestoreClient()
    _seed_audit_catalog(client)
    calculator = ArchitectureCostCalculator(
        PricingCatalogRepository(client),
        pricing_profiles=PricingProfileRepository(client),
    )

    components = [
        MappedComponent(
            key="service",
            name="API",
            component_type="api",
            reason="Backend",
            category="core",
            optional=False,
            order=0,
            cloud={"aws": [], "gcp": ["Cloud Run"], "azure": []},
            implementation_options={},
        ),
        MappedComponent(
            key="object_storage",
            name="Object Storage",
            component_type="object_storage",
            reason="Files",
            category="core",
            optional=True,
            order=1,
            cloud={"aws": [], "gcp": ["Cloud Storage"], "azure": []},
            implementation_options={},
        ),
    ]

    results = calculator.calculate(components=components, expected_users="100", stage="mvp")
    gcp = next(r for r in results if r.provider == "gcp")

    assert len(gcp.component_breakdown) == 2
    api_breakdown = next(b for b in gcp.component_breakdown if b["component_key"] == "service")
    storage_breakdown = next(b for b in gcp.component_breakdown if b["component_key"] == "object_storage")

    assert api_breakdown["pricing_model"] == PRICING_MODEL_COMPUTE_REQUEST
    assert api_breakdown["selected_cloud_service"] == "Cloud Run"
    assert "cpu_seconds" in api_breakdown["usage_assumptions"]
    assert len(api_breakdown["sku_lines"]) >= 3

    assert storage_breakdown["pricing_model"] == PRICING_MODEL_STORAGE
    assert storage_breakdown["usage_assumptions"]["storage_gb"] > 0
