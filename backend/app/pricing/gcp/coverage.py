"""GCP pricing coverage inventory and gap classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.pricing.gcp.allowances import FREE_TIER_POOLS
from app.pricing.gcp.registry import get_gcp_pricing_model, list_gcp_pricing_models, normalize_gcp_service_name
from app.pricing.gcp.sku_quantities.calculator import _CALCULATORS
from app.pricing.gcp.sku_roles import _SKU_ROLE_OVERRIDES
from app.pricing.gcp.ui_only import is_gcp_ui_only_service, ui_only_note_for_service
from app.pricing.usage.gcp_behavioral_models import GCP_BEHAVIORAL_MODELS

CoverageGroup = Literal["A", "B", "C", "D", "E", "U"]

DEFERRED_GCP_SERVICES: dict[str, str] = {}

TEST_FIXTURE_CATALOG_SERVICES: frozenset[str] = frozenset(
    {
        "API Gateway",
        "BigQuery",
        "Cloud Firestore",
        "Cloud Logging",
        "Cloud Memorystore for Redis",
        "Cloud Monitoring",
        "Cloud Pub/Sub",
        "Cloud Run",
        "Cloud Run Functions",
        "Cloud SQL",
        "Cloud Storage",
        "Cloud Tasks",
        "Cloud Trace",
        "Firebase",
        "Firebase Hosting",
        "Gemini API",
        "Networking",
        "Secret Manager",
        "Vertex AI",
        "Vertex AI Search",
    }
)


class CoverageGap(str, Enum):
    PRICING_MODEL = "missing_pricing_model"
    SKU_CALCULATOR = "missing_sku_calculator"
    SKU_ROLES = "missing_sku_role_mapping"
    BEHAVIORAL_MODEL = "missing_behavioral_model"
    FREE_TIER = "missing_free_tier"
    CATALOG_FIXTURE = "missing_test_catalog_fixture"
    DEFERRED = "deferred_complex_pricing"


@dataclass(frozen=True)
class CatalogGcpServiceEntry:
    service_name: str
    api_service_code: str
    component_types: tuple[str, ...]
    is_default_for_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class GcpServiceCoverage:
    service_name: str
    canonical_service: str
    component_types: tuple[str, ...]
    is_default_mapping: bool
    pricing_model: bool
    sku_calculator: bool
    sku_role_mapping: bool
    behavioral_model: bool
    free_tier: bool
    test_catalog_fixture: bool
    fully_supported: bool
    coverage_group: CoverageGroup
    gaps: tuple[str, ...] = ()
    deferred_reason: str | None = None
    fallback_behavior: str = ""

    def missing_implementation(self) -> list[str]:
        items: list[str] = []
        if not self.pricing_model:
            items.append("pricing_model_definition")
        if not self.sku_calculator:
            items.append("sku_quantity_calculator")
        if not self.sku_role_mapping:
            items.append("sku_role_mapping")
        if not self.behavioral_model:
            items.append("behavioral_usage_model")
        if not self.free_tier and self.pricing_model:
            items.append("free_tier_allowances")
        if not self.test_catalog_fixture and self.fully_supported:
            items.append("test_catalog_fixture")
        return items


@dataclass
class GcpPricingCoverageReport:
    services: list[GcpServiceCoverage] = field(default_factory=list)
    by_group: dict[str, list[str]] = field(default_factory=dict)

    @property
    def fully_supported(self) -> list[str]:
        return [s.service_name for s in self.services if s.coverage_group == "A"]

    @property
    def unsupported(self) -> list[str]:
        return [s.service_name for s in self.services if s.coverage_group in {"C", "D", "E"}]

    @property
    def ui_only(self) -> list[str]:
        return [s.service_name for s in self.services if s.coverage_group == "U"]


def collect_catalog_gcp_services() -> list[CatalogGcpServiceEntry]:
    """Collect unique GCP services from component_catalog_seed with component types."""
    by_name: dict[str, dict[str, Any]] = {}

    for entry in COMPONENT_CATALOG_SEED:
        component_type = str(entry["name"])
        gcp_options = entry.get("gcp_options") or []
        for idx, raw in enumerate(gcp_options):
            if isinstance(raw, str):
                name = raw.strip()
                api_service_code = ""
            elif isinstance(raw, dict):
                name = str(raw.get("name", "")).strip()
                api_service_code = str(raw.get("api_service_code", ""))
            else:
                continue
            if not name or name in {"N/A", "Third-party API", "Stripe", "Paddle", "SendGrid"}:
                continue
            bucket = by_name.setdefault(
                name,
                {
                    "api_service_code": api_service_code,
                    "component_types": set(),
                    "default_for": set(),
                },
            )
            if api_service_code and not bucket["api_service_code"]:
                bucket["api_service_code"] = api_service_code
            bucket["component_types"].add(component_type)
            if idx == 0:
                bucket["default_for"].add(component_type)

    results: list[CatalogGcpServiceEntry] = []
    for name in sorted(by_name.keys(), key=str.casefold):
        data = by_name[name]
        results.append(
            CatalogGcpServiceEntry(
                service_name=name,
                api_service_code=data["api_service_code"],
                component_types=tuple(sorted(data["component_types"])),
                is_default_for_types=tuple(sorted(data["default_for"])),
            )
        )
    return results


def _has_sku_role_mapping(canonical: str) -> bool:
    if canonical in _SKU_ROLE_OVERRIDES:
        return True
    model = get_gcp_pricing_model(canonical)
    if model is None:
        return False
    return any(sku.catalog_sku_roles for sku in model.pricing_model.calculated_skus)


def _has_free_tier(canonical: str) -> bool:
    model = get_gcp_pricing_model(canonical)
    if model is None:
        return False
    return model.pricing_model.free_tier is not None


def _fallback_behavior(coverage: GcpServiceCoverage) -> str:
    if coverage.coverage_group == "U":
        return (
            "UI-only service: $0 component cost in catalog pipeline; "
            "bill analytics through connected data sources (e.g. BigQuery)."
        )
    if coverage.fully_supported:
        return "Catalog pipeline: usage inference → SKU quantities → free tier → gcp_catalog → cost."
    if coverage.deferred_reason:
        return f"Explicit unsupported (deferred): {coverage.deferred_reason}"
    if not coverage.pricing_model:
        return (
            "Explicit unsupported: component appears in pricing output with "
            "pricing_status=unsupported; not silently omitted or heuristic-priced."
        )
    return (
        "Explicit unsupported (partial implementation): pricing_status=unsupported "
        "with missing implementation details."
    )


def _classify_service(
    entry: CatalogGcpServiceEntry,
    *,
    pricing_model: bool,
    sku_calculator: bool,
    sku_role_mapping: bool,
    behavioral_model: bool,
    free_tier: bool,
    test_catalog_fixture: bool,
    deferred_reason: str | None,
) -> tuple[CoverageGroup, tuple[str, ...], bool]:
    gaps: list[str] = []
    if deferred_reason:
        return "E", (CoverageGap.DEFERRED.value,), False

    if not pricing_model:
        gaps.append(CoverageGap.PRICING_MODEL.value)
        return "C", tuple(gaps), False

    if not sku_calculator:
        gaps.append(CoverageGap.SKU_CALCULATOR.value)
    if not sku_role_mapping:
        gaps.append(CoverageGap.SKU_ROLES.value)
    if not behavioral_model:
        gaps.append(CoverageGap.BEHAVIORAL_MODEL.value)

    if pricing_model and sku_calculator and sku_role_mapping and behavioral_model:
        if not free_tier:
            gaps.append(CoverageGap.FREE_TIER.value)
        if not test_catalog_fixture:
            gaps.append(CoverageGap.CATALOG_FIXTURE.value)
        if not gaps:
            return "A", (), True
        if sku_calculator and sku_role_mapping and behavioral_model:
            return "B", tuple(gaps), False

    return "D", tuple(gaps), False


def inspect_gcp_service_coverage(service_name: str) -> GcpServiceCoverage:
    catalog_entries = {e.service_name: e for e in collect_catalog_gcp_services()}
    entry = catalog_entries.get(service_name)
    canonical = normalize_gcp_service_name(service_name)

    if is_gcp_ui_only_service(service_name):
        return GcpServiceCoverage(
            service_name=service_name,
            canonical_service=canonical,
            component_types=entry.component_types if entry else (),
            is_default_mapping=bool(entry and entry.is_default_for_types),
            pricing_model=False,
            sku_calculator=False,
            sku_role_mapping=False,
            behavioral_model=False,
            free_tier=False,
            test_catalog_fixture=False,
            fully_supported=False,
            coverage_group="U",
            gaps=(),
            deferred_reason=None,
            fallback_behavior=(
                "UI-only service: $0 component cost in catalog pipeline; "
                "bill analytics through connected data sources (e.g. BigQuery)."
            ),
        )

    deferred = DEFERRED_GCP_SERVICES.get(service_name) or DEFERRED_GCP_SERVICES.get(canonical)

    pricing_model = get_gcp_pricing_model(service_name) is not None
    sku_calculator = canonical in _CALCULATORS
    sku_role_mapping = _has_sku_role_mapping(canonical)
    behavioral_model = canonical in GCP_BEHAVIORAL_MODELS
    free_tier = _has_free_tier(canonical)
    test_catalog_fixture = canonical in TEST_FIXTURE_CATALOG_SERVICES

    group, gaps, fully_supported = _classify_service(
        entry or CatalogGcpServiceEntry(service_name, "", ()),
        pricing_model=pricing_model,
        sku_calculator=sku_calculator,
        sku_role_mapping=sku_role_mapping,
        behavioral_model=behavioral_model,
        free_tier=free_tier,
        test_catalog_fixture=test_catalog_fixture,
        deferred_reason=deferred,
    )

    coverage = GcpServiceCoverage(
        service_name=service_name,
        canonical_service=canonical,
        component_types=entry.component_types if entry else (),
        is_default_mapping=bool(entry and entry.is_default_for_types),
        pricing_model=pricing_model,
        sku_calculator=sku_calculator,
        sku_role_mapping=sku_role_mapping,
        behavioral_model=behavioral_model,
        free_tier=free_tier,
        test_catalog_fixture=test_catalog_fixture,
        fully_supported=fully_supported,
        coverage_group=group,
        gaps=gaps,
        deferred_reason=deferred,
    )
    return GcpServiceCoverage(
        service_name=coverage.service_name,
        canonical_service=coverage.canonical_service,
        component_types=coverage.component_types,
        is_default_mapping=coverage.is_default_mapping,
        pricing_model=coverage.pricing_model,
        sku_calculator=coverage.sku_calculator,
        sku_role_mapping=coverage.sku_role_mapping,
        behavioral_model=coverage.behavioral_model,
        free_tier=coverage.free_tier,
        test_catalog_fixture=coverage.test_catalog_fixture,
        fully_supported=coverage.fully_supported,
        coverage_group=coverage.coverage_group,
        gaps=coverage.gaps,
        deferred_reason=coverage.deferred_reason,
        fallback_behavior=_fallback_behavior(coverage),
    )


def is_gcp_service_fully_supported(service_name: str) -> bool:
    if is_gcp_ui_only_service(service_name):
        return False
    return inspect_gcp_service_coverage(service_name).fully_supported


def build_gcp_pricing_coverage_report() -> GcpPricingCoverageReport:
    services = [inspect_gcp_service_coverage(entry.service_name) for entry in collect_catalog_gcp_services()]
    by_group: dict[str, list[str]] = {
        "A_fully_supported": [],
        "B_partially_supported": [],
        "C_missing_pricing_model": [],
        "D_missing_catalog_mapping": [],
        "E_deferred_complex": [],
        "U_ui_only": [],
    }
    for item in services:
        key = {
            "A": "A_fully_supported",
            "B": "B_partially_supported",
            "C": "C_missing_pricing_model",
            "D": "D_missing_catalog_mapping",
            "E": "E_deferred_complex",
            "U": "U_ui_only",
        }[item.coverage_group]
        by_group[key].append(item.service_name)

    return GcpPricingCoverageReport(services=services, by_group=by_group)


def unsupported_reason_for_service(service_name: str) -> tuple[str, list[str]]:
    if is_gcp_ui_only_service(service_name):
        return ui_only_note_for_service(service_name), []
    cov = inspect_gcp_service_coverage(service_name)
    if cov.fully_supported:
        return "", []

    if cov.deferred_reason:
        return cov.deferred_reason, list(cov.gaps)

    missing = cov.missing_implementation()
    if not cov.pricing_model:
        return (
            f"GCP catalog pricing is not implemented for {service_name!r}.",
            missing or ["pricing_model_definition"],
        )
    return (
        f"GCP catalog pricing for {service_name!r} is incomplete.",
        missing or list(cov.gaps),
    )


def list_fully_supported_gcp_services() -> list[str]:
    return sorted({m.service for m in list_gcp_pricing_models() if is_gcp_service_fully_supported(m.service)})
