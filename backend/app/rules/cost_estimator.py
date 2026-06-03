"""Deterministic monthly cost estimator.

Important: these are rough estimated ranges derived from static configuration,
NOT live billing numbers. The estimator multiplies a per-provider baseline by a
user-tier factor and adds feature/stage bands. The structure is intentionally
simple and swappable so live cloud pricing APIs can replace it later.
"""

from __future__ import annotations

from dataclasses import dataclass

PROVIDERS = ("aws", "gcp", "azure")

# Baseline monthly range (low, high) for a minimal app: API + service + DB + client.
_BASELINE: dict[str, tuple[float, float]] = {
    "aws": (15, 45),
    "gcp": (12, 40),
    "azure": (18, 50),
}

# Feature add-on bands (low, high) per provider.
_FEATURE_BANDS: dict[str, dict[str, tuple[float, float]]] = {
    "file_upload": {"aws": (5, 20), "gcp": (4, 18), "azure": (5, 22)},
    "ai": {"aws": (20, 120), "gcp": (18, 110), "azure": (22, 130)},
    "background_processing": {"aws": (8, 30), "gcp": (7, 28), "azure": (9, 32)},
}

# Production adds operational components (monitoring, logging, backup, security).
_PRODUCTION_BAND: dict[str, tuple[float, float]] = {
    "aws": (15, 60),
    "gcp": (12, 55),
    "azure": (16, 65),
}

# Expected-users tier scales the whole estimate.
_USER_MULTIPLIER: dict[str, float] = {
    "100": 1.0,
    "1000": 1.8,
    "10000": 4.0,
    "100000+": 9.0,
}

_PROVIDER_LABEL = {"aws": "AWS", "gcp": "Google Cloud", "azure": "Azure"}


@dataclass
class ProviderCost:
    provider: str
    monthly_low: float
    monthly_high: float
    currency: str
    notes: str


def estimate_costs(
    *,
    expected_users: str,
    stage: str,
    file_upload: bool,
    ai: bool,
    background_processing: bool,
) -> list[ProviderCost]:
    multiplier = _USER_MULTIPLIER.get(expected_users, 1.0)
    results: list[ProviderCost] = []

    for provider in PROVIDERS:
        low, high = _BASELINE[provider]

        if file_upload:
            fl, fh = _FEATURE_BANDS["file_upload"][provider]
            low, high = low + fl, high + fh
        if ai:
            al, ah = _FEATURE_BANDS["ai"][provider]
            low, high = low + al, high + ah
        if background_processing:
            bl, bh = _FEATURE_BANDS["background_processing"][provider]
            low, high = low + bl, high + bh
        if stage == "production":
            pl, ph = _PRODUCTION_BAND[provider]
            low, high = low + pl, high + ph

        low = round(low * multiplier)
        high = round(high * multiplier)

        results.append(
            ProviderCost(
                provider=provider,
                monthly_low=float(low),
                monthly_high=float(high),
                currency="USD",
                notes=(
                    f"Estimated range for {_PROVIDER_LABEL[provider]} at "
                    f"~{expected_users} users ({stage}). Estimate only, not exact billing."
                ),
            )
        )

    return results
