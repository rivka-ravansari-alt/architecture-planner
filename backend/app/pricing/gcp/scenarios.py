"""GCP benchmark scenarios reusing Azure architecture definitions with GCP mappings."""

from __future__ import annotations

from app.pricing.aws.scenarios import AWS_TWENTY_SCENARIOS
from app.pricing.azure.scenarios import (
    ALL_BENCHMARK_SCENARIOS,
    BenchmarkScenario,
    _mapped_components,
)

GCP_CORE_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = ALL_BENCHMARK_SCENARIOS[:5]

GCP_PLATFORM_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = tuple(
    scenario
    for scenario in AWS_TWENTY_SCENARIOS
    if scenario.scenario_id
    in {
        "mobile_wellness",
        "enterprise_web_platform",
        "ai_analytics_suite",
        "marketplace_search_email",
        "cloud_native_microservices",
    }
)

GCP_TWENTY_SCENARIOS: tuple[BenchmarkScenario, ...] = AWS_TWENTY_SCENARIOS

GCP_EXTENDED_SERVICES: frozenset[str] = frozenset(
    {
        "BigQuery",
        "Cloud Logging",
        "Cloud Monitoring",
        "Cloud Trace",
        "Firebase",
        "Firebase Hosting",
        "Gemini API",
        "Vertex AI",
        "Vertex AI Search",
    }
)


def gcp_scenario_components(scenario: BenchmarkScenario) -> list:
    """Return MappedComponent list with GCP cloud mappings."""
    return _mapped_components(scenario.components)


def normalize_gcp_service_aliases(service_name: str) -> str:
    """Normalize shorthand GCP service names from legacy scenarios."""
    aliases = {
        "pub/sub": "Cloud Pub/Sub",
        "cloud pubsub": "Cloud Pub/Sub",
    }
    return aliases.get(service_name.strip().casefold(), service_name)
