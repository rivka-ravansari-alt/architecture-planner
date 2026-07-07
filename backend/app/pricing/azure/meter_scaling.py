"""Normalize billable SKU quantity units to Firestore catalog usage_unit meters."""

from __future__ import annotations

import re


class MeterUnitScaler:
    """Convert quantity units to catalog meter units before cost multiplication."""

    _PER_10K_PATTERN = re.compile(r"10\s*,?\s*0{3}|10\s*k\b", re.IGNORECASE)
    _PER_1M_PATTERN = re.compile(r"\b1\s*m\b|1\s*,?\s*0{6}\b", re.IGNORECASE)
    _PER_HOUR_PATTERN = re.compile(r"\b1\s+hour\b|\bhour\b", re.IGNORECASE)
    _GB_MONTH_PATTERN = re.compile(r"gb\s*/?\s*month|gb-month", re.IGNORECASE)
    _GB_PATTERN = re.compile(r"\bgb\b|gib", re.IGNORECASE)
    _SECONDS_PATTERN = re.compile(r"second", re.IGNORECASE)
    _EXECUTION_PATTERN = re.compile(r"execution", re.IGNORECASE)
    _REQUEST_PATTERN = re.compile(r"request", re.IGNORECASE)
    _OPERATION_PATTERN = re.compile(r"operation", re.IGNORECASE)
    _CONNECTION_PATTERN = re.compile(r"connection", re.IGNORECASE)
    _INSTANCE_MONTH_PATTERN = re.compile(r"instance", re.IGNORECASE)

    def scale(
        self,
        quantity: float,
        quantity_unit: str,
        usage_unit: str,
    ) -> tuple[float, str] | None:
        """Return (billable_units, formula_note) or None when pairing is unrecognized."""
        qty_unit = quantity_unit.strip().casefold()
        meter = usage_unit.strip()

        if self._PER_10K_PATTERN.search(meter):
            if "operation" in qty_unit or "request" in qty_unit or "execution" in qty_unit:
                return quantity / 10_000, f"{quantity:,.0f} ops / 10,000"
            return None

        if self._PER_1M_PATTERN.search(meter):
            if (
                "operation" in qty_unit
                or "message" in qty_unit
                or "request" in qty_unit
            ):
                return quantity / 1_000_000, f"{quantity:,.0f} ops / 1,000,000"
            return None

        if self._PER_HOUR_PATTERN.search(meter):
            if "second" in qty_unit:
                return quantity / 3600, f"{quantity:,.0f} seconds / 3600"
            if "hour" in qty_unit:
                return quantity, f"{quantity:,.0f} hours (direct)"
            return None

        if self._GB_MONTH_PATTERN.search(meter) or self._GB_MONTH_PATTERN.search(qty_unit):
            if "gb" in qty_unit or "gib" in qty_unit:
                return quantity, f"{quantity:,.4f} GB-months (direct)"

        if self._GB_PATTERN.search(meter) and ("gb" in qty_unit or "gib" in qty_unit):
            return quantity, f"{quantity:,.4f} GB (direct)"

        if self._EXECUTION_PATTERN.search(meter) and (
            "execution" in qty_unit or "request" in qty_unit
        ):
            return quantity, f"{quantity:,.0f} executions (direct)"

        if self._REQUEST_PATTERN.search(meter) and "request" in qty_unit:
            return quantity, f"{quantity:,.0f} requests (direct)"

        if self._OPERATION_PATTERN.search(meter) and "operation" in qty_unit:
            return quantity, f"{quantity:,.0f} operations (direct)"

        if self._CONNECTION_PATTERN.search(meter) and "connection" in qty_unit:
            return quantity, f"{quantity:,.0f} connections (direct)"

        if self._SECONDS_PATTERN.search(qty_unit) and (
            "second" in meter.casefold() or "vcpu" in meter.casefold()
        ):
            return quantity, f"{quantity:,.0f} seconds (direct)"

        if self._INSTANCE_MONTH_PATTERN.search(qty_unit) and "month" in meter.casefold():
            return quantity, f"{quantity:,.0f} instance-months (direct)"

        # Fallback: identical unit families (month, unit count).
        if "month" in qty_unit and "month" in meter.casefold():
            return quantity, f"{quantity:,.4f} (monthly direct)"

        return None
