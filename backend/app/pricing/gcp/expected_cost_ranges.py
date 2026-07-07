"""Engineering-judgment expected monthly GCP cost ranges for benchmark scenarios."""

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


EXPECTED_COST_RANGES: dict[str, dict[int, ExpectedCostRange]] = {
    "simple_crud_saas": {
        100: ExpectedCostRange(25, 55, "Cloud SQL micro floor + light Cloud Run usage"),
        1_000: ExpectedCostRange(70, 140, "Fixed SQL tier dominates; modest API scaling"),
        10_000: ExpectedCostRange(550, 1_100, "Request/compute scaling; SQL still micro/small"),
        100_000: ExpectedCostRange(5_500, 9_500, "High API + storage; SQL instance still flat"),
    },
    "self_esteem_habit": {
        100: ExpectedCostRange(25, 60, "Same core stack as CRUD SaaS plus small Pub/Sub cost"),
        1_000: ExpectedCostRange(75, 150, "Background jobs add margin over CRUD"),
        10_000: ExpectedCostRange(600, 1_200, "Growing API + messaging ops"),
        100_000: ExpectedCostRange(5_500, 9_500, "Messaging + API at scale"),
    },
    "ecommerce": {
        100: ExpectedCostRange(35, 85, "Extra Functions + Pub/Sub over CRUD baseline"),
        1_000: ExpectedCostRange(160, 330, "File uploads + messaging increase storage/ops"),
        10_000: ExpectedCostRange(1_600, 3_000, "Product media + order events scale"),
        100_000: ExpectedCostRange(16_000, 28_000, "Storage + messaging dominate at scale"),
    },
    "ai_chat": {
        100: ExpectedCostRange(25, 65, "Elevated API traffic; Gemini/Vertex token costs modest at MVP"),
        1_000: ExpectedCostRange(85, 170, "Cloud Run + API for chat sessions"),
        10_000: ExpectedCostRange(650, 1_300, "Higher request volume + AI tokens"),
        100_000: ExpectedCostRange(7_500, 14_000, "Streaming API + worker invocations at scale"),
    },
    "ai_document_ocr": {
        100: ExpectedCostRange(5, 22, "Async workers; low traffic MVP"),
        1_000: ExpectedCostRange(65, 150, "Document storage + Tasks + Functions"),
        10_000: ExpectedCostRange(750, 1_400, "Upload volume drives GCS + queue"),
        100_000: ExpectedCostRange(7_500, 13_000, "Storage-heavy OCR pipeline"),
    },
}


def get_expected_range(scenario_id: str, users: int) -> ExpectedCostRange | None:
    by_users = EXPECTED_COST_RANGES.get(scenario_id)
    if by_users is None:
        return None
    return by_users.get(users)


def evaluate_expected_cost(
    scenario_id: str,
    users: int,
    actual_usd: float,
) -> tuple[ExpectedCostRange | None, bool | None]:
    expected = get_expected_range(scenario_id, users)
    if expected is None:
        return None, None
    return expected, expected.contains(actual_usd)
