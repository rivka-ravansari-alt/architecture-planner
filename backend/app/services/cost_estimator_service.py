"""Deterministic monthly cost estimation."""

from __future__ import annotations

from app.config.params import (
    CLOUD_PROVIDERS,
    CLOUD_PROVIDER_LABELS,
    COST_BASELINE,
    COST_CURRENCY,
    COST_FEATURE_BANDS,
    COST_PRODUCTION_BAND,
    COST_USER_MULTIPLIER,
    FEATURE_FLAG_KEYS,
    STAGE_PRODUCTION,
)
from app.schemas.domain import ProviderCost


class CostEstimatorService:
    def estimate(
        self,
        *,
        expected_users: str,
        stage: str,
        file_upload: bool,
        ai: bool,
        background_processing: bool,
    ) -> list[ProviderCost]:
        multiplier = COST_USER_MULTIPLIER.get(expected_users, 1.0)
        flags = {
            "file_upload": file_upload,
            "ai": ai,
            "background_processing": background_processing,
        }
        return [
            self._estimate_for_provider(provider, stage, flags, multiplier, expected_users)
            for provider in CLOUD_PROVIDERS
        ]

    def _estimate_for_provider(
        self,
        provider: str,
        stage: str,
        flags: dict[str, bool],
        multiplier: float,
        expected_users: str,
    ) -> ProviderCost:
        low, high = COST_BASELINE[provider]
        low, high = self._apply_feature_bands(provider, flags, low, high)
        if stage == STAGE_PRODUCTION:
            low, high = self._apply_production_band(provider, low, high)
        low, high = self._apply_user_multiplier(low, high, multiplier)
        return ProviderCost(
            provider=provider,
            monthly_low=float(low),
            monthly_high=float(high),
            currency=COST_CURRENCY,
            notes=self._build_notes(provider, expected_users, stage),
        )

    def _apply_feature_bands(
        self,
        provider: str,
        flags: dict[str, bool],
        low: float,
        high: float,
    ) -> tuple[float, float]:
        for feature_key in FEATURE_FLAG_KEYS:
            if flags.get(feature_key):
                band_low, band_high = COST_FEATURE_BANDS[feature_key][provider]
                low += band_low
                high += band_high
        return low, high

    @staticmethod
    def _apply_production_band(
        provider: str,
        low: float,
        high: float,
    ) -> tuple[float, float]:
        prod_low, prod_high = COST_PRODUCTION_BAND[provider]
        return low + prod_low, high + prod_high

    @staticmethod
    def _apply_user_multiplier(low: float, high: float, multiplier: float) -> tuple[int, int]:
        return round(low * multiplier), round(high * multiplier)

    @staticmethod
    def _build_notes(provider: str, expected_users: str, stage: str) -> str:
        label = CLOUD_PROVIDER_LABELS[provider]
        return (
            f"Estimated range for {label} at ~{expected_users} users ({stage}). "
            "Estimate only, not exact billing."
        )
