"""Engineering-judgment expected monthly Azure cost ranges for benchmark scenarios.

Ranges are intentionally approximate — they encode Azure pricing guidance and
product intuition, not exact calculator output. Actual costs outside a range
produce a validation warning, not a hard failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.pricing.azure.benchmark import BENCHMARK_USER_COUNTS


@dataclass(frozen=True)
class ExpectedCostRange:
    """Inclusive USD/month range for one scenario at one user count."""

    min_usd: float
    max_usd: float
    rationale: str = ""

    @property
    def label(self) -> str:
        return f"${self.min_usd:,.0f}-${self.max_usd:,.0f}"

    def contains(self, actual_usd: float) -> bool:
        return self.min_usd <= actual_usd <= self.max_usd


# scenario_id -> users -> range
EXPECTED_COST_RANGES: dict[str, dict[int, ExpectedCostRange]] = {
    "simple_crud_saas": {
        100: ExpectedCostRange(30, 60, "SQL S1 floor (~$30) + light Container Apps usage"),
        1_000: ExpectedCostRange(80, 150, "Fixed SQL tier dominates; modest API scaling"),
        10_000: ExpectedCostRange(600, 1_200, "Request/compute scaling; SQL still S1"),
        100_000: ExpectedCostRange(6_000, 10_000, "High API + storage; SQL instance still flat"),
    },
    "self_esteem_habit": {
        100: ExpectedCostRange(30, 65, "Same core stack as CRUD SaaS plus small queue cost"),
        1_000: ExpectedCostRange(85, 160, "Queue background jobs add margin over CRUD"),
        10_000: ExpectedCostRange(650, 1_250, "Growing API + queue ops"),
        100_000: ExpectedCostRange(6_000, 10_000, "Queue + API at scale; SQL S1 floor"),
    },
    "ecommerce": {
        100: ExpectedCostRange(40, 90, "Extra Functions + Service Bus over CRUD baseline"),
        1_000: ExpectedCostRange(180, 350, "File uploads + messaging increase storage/ops"),
        10_000: ExpectedCostRange(1_800, 3_200, "Product media + order events scale"),
        100_000: ExpectedCostRange(18_000, 30_000, "Storage + messaging dominate at scale"),
    },
    "ai_chat": {
        100: ExpectedCostRange(30, 70, "Elevated API traffic; Azure-only (no external LLM)"),
        1_000: ExpectedCostRange(90, 180, "Functions + API for chat sessions"),
        10_000: ExpectedCostRange(700, 1_400, "Higher request volume; still no LLM passthrough"),
        100_000: ExpectedCostRange(8_000, 15_000, "Streaming API + worker invocations at scale"),
    },
    "ai_document_ocr": {
        100: ExpectedCostRange(5, 25, "Async workers; low traffic MVP"),
        1_000: ExpectedCostRange(70, 160, "Document storage + queue + Functions"),
        10_000: ExpectedCostRange(800, 1_500, "Upload volume drives Blob + queue"),
        100_000: ExpectedCostRange(8_000, 14_000, "Storage-heavy OCR pipeline"),
    },
    "file_storage_drive": {
        100: ExpectedCostRange(30, 70, "SQL floor + modest per-user blob"),
        1_000: ExpectedCostRange(150, 320, "Storage begins to dominate over SQL"),
        10_000: ExpectedCostRange(1_800, 3_000, "Blob storage is primary driver"),
        100_000: ExpectedCostRange(18_000, 28_000, "Linear storage growth with users"),
    },
    "social_network": {
        100: ExpectedCostRange(40, 85, "Media uploads + Service Bus over CRUD"),
        1_000: ExpectedCostRange(170, 330, "Feed reads + blob media"),
        10_000: ExpectedCostRange(1_900, 3_100, "Messaging + storage at scale"),
        100_000: ExpectedCostRange(18_000, 28_000, "Similar to drive + event fan-out"),
    },
    "video_processing": {
        100: ExpectedCostRange(5, 25, "Async video pipeline at MVP scale"),
        1_000: ExpectedCostRange(70, 160, "Blob + queue + transcode workers"),
        10_000: ExpectedCostRange(800, 1_500, "Large object storage accumulation"),
        100_000: ExpectedCostRange(8_000, 14_000, "Video storage dominates (transcode stub)"),
    },
    "background_job_platform": {
        100: ExpectedCostRange(10, 35, "No SQL; messaging + Functions only"),
        1_000: ExpectedCostRange(50, 120, "Dual queue + Service Bus baseline"),
        10_000: ExpectedCostRange(450, 900, "Job throughput scales messaging"),
        100_000: ExpectedCostRange(5_000, 9_000, "Functions + messaging at high volume"),
    },
    "analytics_dashboard": {
        100: ExpectedCostRange(30, 60, "Read-heavy CRUD-like profile"),
        1_000: ExpectedCostRange(80, 150, "SQL S1 + dashboard API"),
        10_000: ExpectedCostRange(600, 1_200, "Report exports add blob cost"),
        100_000: ExpectedCostRange(6_000, 10_000, "Same shape as Simple CRUD SaaS"),
    },
    "static_website": {
        100: ExpectedCostRange(2, 15, "No database; Blob + minimal Functions"),
        1_000: ExpectedCostRange(25, 60, "Static asset egress + form submissions"),
        10_000: ExpectedCostRange(250, 550, "CDN-like read traffic on Blob"),
        100_000: ExpectedCostRange(2_500, 5_500, "High page-view storage/egress (no SQL floor)"),
    },
}


def get_expected_range(scenario_id: str, users: int) -> ExpectedCostRange | None:
    """Return the expected range for a scenario/user count, if defined."""
    by_users = EXPECTED_COST_RANGES.get(scenario_id)
    if by_users is None:
        return None
    return by_users.get(users)


def evaluate_expected_cost(
    scenario_id: str,
    users: int,
    actual_usd: float,
) -> tuple[ExpectedCostRange | None, bool | None]:
    """Return (range, in_range). in_range is None when no range is defined."""
    expected = get_expected_range(scenario_id, users)
    if expected is None:
        return None, None
    return expected, expected.contains(actual_usd)
