"""Backward-compatible usage profile access — delegates to UsageEstimator."""

from __future__ import annotations

from app.services.usage_estimation import UsageEstimator


def build_usage_profile(*, expected_users: str, stage: str) -> dict[str, float]:
    """Return global pricing metrics for tests and legacy callers without components."""
    estimate = UsageEstimator().estimate(
        expected_users=expected_users,
        stage=stage,
        components=[],
    )
    return estimate.global_consumption.to_pricing_metrics()
