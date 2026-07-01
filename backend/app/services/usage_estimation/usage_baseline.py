"""Shared baseline usage helpers (no allocator/estimator dependencies)."""

from __future__ import annotations

from app.config.params import STAGE_PRODUCTION, USAGE_ESTIMATION_BASE


def parse_active_user_count(expected_users: str) -> int:
    normalized = expected_users.strip().rstrip("+")
    try:
        return max(1, int(normalized))
    except ValueError:
        return 100


def resolve_hosting_instance_metrics(users: int, stage: str) -> tuple[float, float]:
    """Tier-scaled hosting instance usage — avoids 24/7 billing for small startups."""
    base = USAGE_ESTIMATION_BASE
    cap = base.get("hosting_instance_hours_cap", 72.0)
    full_hours = base.get("instance_hours_full", 720.0)

    if users <= 100:
        hours = min(cap, max(24.0, users * 0.72))
        instances = 0.0
    elif users <= 1000:
        hours = min(360.0, max(cap, users * 0.15))
        instances = 1.0 if stage == STAGE_PRODUCTION else 0.0
    else:
        hours = full_hours
        instances = max(1.0, users / 5000.0)
    return hours, instances
