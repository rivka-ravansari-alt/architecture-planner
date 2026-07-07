"""Normalize billable SKU quantity units to Firestore catalog usage_unit meters."""

from __future__ import annotations

import re


class GcpMeterUnitScaler:
    """Convert quantity units to catalog meter units before cost multiplication."""

    _PER_10K_PATTERN = re.compile(r"10\s*,?\s*0{3}|10\s*k\b", re.IGNORECASE)
    _PER_1K_PATTERN = re.compile(r"\b1\s*k\b|1\s*,?\s*0{3}\b", re.IGNORECASE)
    _PER_1M_PATTERN = re.compile(r"\b1\s*m\b|1\s*,?\s*0{6}\b", re.IGNORECASE)
    _TB_PATTERN = re.compile(r"\btb\b|terabyte", re.IGNORECASE)
    _TOKEN_PATTERN = re.compile(r"\btoken", re.IGNORECASE)
    _MINUTE_PATTERN = re.compile(r"\bminute", re.IGNORECASE)
    _TRACE_PATTERN = re.compile(r"\btrace|\bspan", re.IGNORECASE)
    _EMAIL_PATTERN = re.compile(r"\bemail", re.IGNORECASE)
    _SEAT_PATTERN = re.compile(r"\bseat", re.IGNORECASE)
    _GB_SECOND_PATTERN = re.compile(r"gb[\s-]*second|gb[\s-]*s\b", re.IGNORECASE)
    _HRS_METER_PATTERN = re.compile(r"\bhrs\b", re.IGNORECASE)
    _HOUR_PATTERN = re.compile(r"\bhour", re.IGNORECASE)
    _GB_MONTH_PATTERN = re.compile(r"gb[\s-]*(?:/month|month|mo\b)", re.IGNORECASE)
    _GB_PATTERN = re.compile(r"\bgb\b|gib", re.IGNORECASE)
    _REQUEST_PATTERN = re.compile(r"request|quer", re.IGNORECASE)
    _OPERATION_PATTERN = re.compile(r"operation", re.IGNORECASE)
    _EXECUTION_PATTERN = re.compile(r"execution", re.IGNORECASE)
    _MESSAGE_PATTERN = re.compile(r"message", re.IGNORECASE)

    def scale(
        self,
        quantity: float,
        quantity_unit: str,
        usage_unit: str,
    ) -> tuple[float, str] | None:
        qty_unit = quantity_unit.strip().casefold()
        meter = usage_unit.strip()
        meter_cf = meter.casefold()

        if self._PER_1M_PATTERN.search(meter):
            if (
                "operation" in qty_unit
                or "request" in qty_unit
                or "execution" in qty_unit
                or "message" in qty_unit
                or "quer" in qty_unit
                or "span" in qty_unit
            ):
                return quantity / 1_000_000, f"{quantity:,.0f} ops / 1,000,000"
            if "token" in qty_unit or "trace" in qty_unit:
                return quantity / 1_000_000, f"{quantity:,.0f} / 1,000,000"
            return None

        if self._TB_PATTERN.search(meter) and "tb" in qty_unit:
            return quantity, f"{quantity:,.4f} TB (direct)"

        if self._TOKEN_PATTERN.search(meter) and "token" in qty_unit:
            if self._PER_1K_PATTERN.search(meter):
                return quantity / 1_000, f"{quantity:,.0f} tokens / 1,000"
            return quantity, f"{quantity:,.0f} tokens (direct)"

        if self._MINUTE_PATTERN.search(meter) and "minute" in qty_unit:
            return quantity, f"{quantity:,.0f} minutes (direct)"

        if self._TRACE_PATTERN.search(meter) and ("trace" in qty_unit or "span" in qty_unit):
            if self._PER_1M_PATTERN.search(meter):
                return quantity / 1_000_000, f"{quantity:,.0f} spans / 1,000,000"
            return quantity, f"{quantity:,.0f} spans (direct)"

        if self._EMAIL_PATTERN.search(meter) and "email" in qty_unit:
            if self._PER_1K_PATTERN.search(meter):
                return quantity / 1_000, f"{quantity:,.0f} emails / 1,000"
            return quantity, f"{quantity:,.0f} emails (direct)"

        if self._SEAT_PATTERN.search(meter) and "seat" in qty_unit:
            return quantity, f"{quantity:,.0f} seats (direct)"

        if self._PER_10K_PATTERN.search(meter):
            if (
                "operation" in qty_unit
                or "request" in qty_unit
                or "execution" in qty_unit
                or "message" in qty_unit
            ):
                return quantity / 10_000, f"{quantity:,.0f} ops / 10,000"
            return None

        if self._PER_1K_PATTERN.search(meter):
            if "operation" in qty_unit or "request" in qty_unit or "execution" in qty_unit:
                return quantity / 1_000, f"{quantity:,.0f} ops / 1,000"
            return None

        if self._GB_SECOND_PATTERN.search(meter) and self._GB_SECOND_PATTERN.search(qty_unit):
            return quantity, f"{quantity:,.0f} GB-seconds (direct)"

        if self._HRS_METER_PATTERN.search(meter) and "hour" in qty_unit:
            return quantity, f"{quantity:,.0f} hours (direct)"

        if self._HOUR_PATTERN.search(meter) and "hour" in qty_unit:
            return quantity, f"{quantity:,.0f} hours (direct)"

        if self._HOUR_PATTERN.search(meter) and "second" in qty_unit and "gb" not in qty_unit:
            return quantity / 3600, f"{quantity:,.0f} seconds / 3600"

        if self._GB_MONTH_PATTERN.search(meter) or (
            self._GB_MONTH_PATTERN.search(qty_unit) and "second" not in qty_unit
        ):
            if ("gb" in qty_unit or "gib" in qty_unit) and "second" not in qty_unit:
                return quantity, f"{quantity:,.4f} GB-months (direct)"

        if self._GB_PATTERN.search(meter) and ("gb" in qty_unit or "gib" in qty_unit):
            if "second" not in qty_unit:
                return quantity, f"{quantity:,.4f} GB (direct)"

        if self._REQUEST_PATTERN.search(meter) and (
            "request" in qty_unit
            or "operation" in qty_unit
            or "execution" in qty_unit
            or "message" in qty_unit
            or "quer" in qty_unit
        ):
            label = "requests"
            if "execution" in qty_unit:
                label = "executions"
            elif "operation" in qty_unit:
                label = "operations"
            elif "message" in qty_unit:
                label = "messages"
            elif "quer" in qty_unit:
                label = "queries"
            return quantity, f"{quantity:,.0f} {label} (direct)"

        if self._OPERATION_PATTERN.search(meter) and (
            "operation" in qty_unit or "request" in qty_unit
        ):
            return quantity, f"{quantity:,.0f} operations (direct)"

        if "month" in qty_unit and "month" in meter_cf:
            return quantity, f"{quantity:,.4f} (monthly direct)"

        if "secret" in qty_unit and "secret" in meter_cf:
            return quantity, f"{quantity:,.0f} secret-months (direct)"

        if "metric" in qty_unit and "metric" in meter_cf:
            return quantity, f"{quantity:,.0f} metrics (direct)"

        if "policy" in qty_unit and ("policy" in meter_cf or "alert" in meter_cf):
            return quantity, f"{quantity:,.0f} policies (direct)"

        return None
