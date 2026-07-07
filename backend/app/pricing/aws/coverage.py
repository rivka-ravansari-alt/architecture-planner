"""AWS pricing coverage inventory and gap classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.pricing.aws.allowances import FREE_TIER_POOLS
from app.pricing.aws.registry import get_aws_pricing_model, list_aws_pricing_models, normalize_aws_service_name
from app.pricing.aws.sku_quantities.calculator import _CALCULATORS
from app.pricing.aws.sku_roles import _SKU_ROLE_OVERRIDES
from app.pricing.usage.aws_behavioral_models import AWS_BEHAVIORAL_MODELS

CoverageGroup = Literal["A", "B", "C", "D", "E"]

# Services intentionally deferred — pricing too complex or out of MVP scope.
DEFERRED_AWS_SERVICES: dict[str, str] = {}

# Catalog services with test-fixture Firestore data (for unit tests).
TEST_FIXTURE_CATALOG_SERVICES: frozenset[str] = frozenset(
    {
        "Lambda",
        "ECS Fargate",
        "RDS",
        "S3",
        "SQS",
        "DynamoDB",
        "API Gateway",
        "SNS",
        "CloudFront",
        "Application Load Balancer",
        "Secrets Manager",
        "Amplify",
        "Amplify Hosting",
        "Bedrock",
        "ElastiCache",
        "OpenSearch Service",
        "Athena",
        "QuickSight",
        "SES",
        "CloudWatch",
        "CloudWatch Logs",
        "CloudWatch Dashboards",
        "CloudWatch Alarms",
        "SSM Parameter Store",
        "AppConfig",
        "X-Ray",
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
class CatalogAwsServiceEntry:
    """One AWS service option from the component catalog seed."""

    service_name: str
    api_service_code: str
    component_types: tuple[str, ...]
    is_default_for_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class AwsServiceCoverage:
    """Implementation coverage for one AWS catalog service."""

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
class AwsPricingCoverageReport:
    """Full AWS pricing coverage report."""

    services: list[AwsServiceCoverage] = field(default_factory=list)
    by_group: dict[str, list[str]] = field(default_factory=dict)

    @property
    def fully_supported(self) -> list[str]:
        return [s.service_name for s in self.services if s.coverage_group == "A"]

    @property
    def unsupported(self) -> list[str]:
        return [s.service_name for s in self.services if s.coverage_group in {"C", "D", "E"}]


def collect_catalog_aws_services() -> list[CatalogAwsServiceEntry]:
    """Collect unique AWS services from component_catalog_seed with component types."""
    by_name: dict[str, dict[str, Any]] = {}

    for entry in COMPONENT_CATALOG_SEED:
        component_type = str(entry["name"])
        aws_options = entry.get("aws_options") or []
        for idx, raw in enumerate(aws_options):
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip()
            if not name or name in {"N/A", "Third-party API", "Stripe", "Paddle"}:
                continue
            bucket = by_name.setdefault(
                name,
                {
                    "api_service_code": str(raw.get("api_service_code", "")),
                    "component_types": set(),
                    "default_for": set(),
                },
            )
            bucket["component_types"].add(component_type)
            if idx == 0:
                bucket["default_for"].add(component_type)

    results: list[CatalogAwsServiceEntry] = []
    for name in sorted(by_name.keys(), key=str.casefold):
        data = by_name[name]
        results.append(
            CatalogAwsServiceEntry(
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
    model = get_aws_pricing_model(canonical)
    if model is None:
        return False
    return any(sku.catalog_sku_roles for sku in model.pricing_model.calculated_skus)


def _has_free_tier(canonical: str) -> bool:
    model = get_aws_pricing_model(canonical)
    if model is None:
        return False
    # Implemented when the pricing model declares a free_tier block (allowances may be empty).
    return model.pricing_model.free_tier is not None


def _fallback_behavior(coverage: AwsServiceCoverage) -> str:
    if coverage.fully_supported:
        return "Catalog pipeline: usage inference → SKU quantities → free tier → aws_catalog → cost."
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
    entry: CatalogAwsServiceEntry,
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


def inspect_aws_service_coverage(service_name: str) -> AwsServiceCoverage:
    """Return coverage details for one catalog AWS service name."""
    catalog_entries = {e.service_name: e for e in collect_catalog_aws_services()}
    entry = catalog_entries.get(service_name)
    canonical = normalize_aws_service_name(service_name)
    deferred = DEFERRED_AWS_SERVICES.get(service_name) or DEFERRED_AWS_SERVICES.get(canonical)

    pricing_model = get_aws_pricing_model(service_name) is not None
    sku_calculator = canonical in _CALCULATORS
    sku_role_mapping = _has_sku_role_mapping(canonical)
    behavioral_model = canonical in AWS_BEHAVIORAL_MODELS
    free_tier = _has_free_tier(canonical)
    test_catalog_fixture = canonical in TEST_FIXTURE_CATALOG_SERVICES

    group, gaps, fully_supported = _classify_service(
        entry or CatalogAwsServiceEntry(service_name, "", ()),
        pricing_model=pricing_model,
        sku_calculator=sku_calculator,
        sku_role_mapping=sku_role_mapping,
        behavioral_model=behavioral_model,
        free_tier=free_tier,
        test_catalog_fixture=test_catalog_fixture,
        deferred_reason=deferred,
    )

    coverage = AwsServiceCoverage(
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
    return AwsServiceCoverage(
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


def is_aws_service_fully_supported(service_name: str) -> bool:
    return inspect_aws_service_coverage(service_name).fully_supported


def build_aws_pricing_coverage_report() -> AwsPricingCoverageReport:
    """Build coverage report for all AWS services in the component catalog."""
    services = [inspect_aws_service_coverage(entry.service_name) for entry in collect_catalog_aws_services()]
    by_group: dict[str, list[str]] = {
        "A_fully_supported": [],
        "B_partially_supported": [],
        "C_missing_pricing_model": [],
        "D_missing_catalog_mapping": [],
        "E_deferred_complex": [],
    }
    for item in services:
        key = {
            "A": "A_fully_supported",
            "B": "B_partially_supported",
            "C": "C_missing_pricing_model",
            "D": "D_missing_catalog_mapping",
            "E": "E_deferred_complex",
        }[item.coverage_group]
        by_group[key].append(item.service_name)

    return AwsPricingCoverageReport(services=services, by_group=by_group)


def unsupported_reason_for_service(service_name: str) -> tuple[str, list[str]]:
    """Return human-readable reason and missing pieces for an unsupported service."""
    cov = inspect_aws_service_coverage(service_name)
    if cov.fully_supported:
        return "", []

    if cov.deferred_reason:
        return cov.deferred_reason, list(cov.gaps)

    missing = cov.missing_implementation()
    if not cov.pricing_model:
        return (
            f"AWS catalog pricing is not implemented for {service_name!r}.",
            missing or ["pricing_model_definition"],
        )
    return (
        f"AWS catalog pricing for {service_name!r} is incomplete.",
        missing or list(cov.gaps),
    )


def list_fully_supported_aws_services() -> list[str]:
    """Return canonical service names with full catalog pricing support."""
    return sorted({m.service for m in list_aws_pricing_models() if is_aws_service_fully_supported(m.service)})
