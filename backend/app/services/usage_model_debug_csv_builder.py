from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.schemas.global_usage_model import GlobalUsageModelPayload
from app.services.usage_inputs_builder import build_usage_inputs


_DERIVED_SMS_DEFAULT_VERIFICATIONS_PER_USER_PER_MONTH = 1.0

# Mirrors `usage_inputs_builder._apply_user_derived_totals()`.
_PER_USER_DERIVED_TOTALS: tuple[tuple[str, str], ...] = (
    ("requests_per_month", "api_requests_per_user_per_month"),
    ("requests_per_month", "requests_per_user_per_month"),
    ("messages_per_month", "messages_per_user_per_month"),
    ("connection_minutes_per_month", "connection_minutes_per_user_per_month"),
    ("reads_per_month", "reads_per_user_per_month"),
    ("writes_per_month", "writes_per_user_per_month"),
    ("request_units_per_month", "request_units_per_user_per_month"),
)


def _is_number(value: Any) -> bool:
    # `bool` is a subclass of `int`; treat it as non-numeric here.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _to_csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        # Stable representation for list-valued parameters (e.g.
        # `authentication_methods`).
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _infer_unit(parameter: str) -> str:
    normalized = (parameter or "").strip()
    if normalized in {"capacity_mode", "workload_type", "api_type", "queue_type"}:
        return ""
    if normalized in {"stage"}:
        return ""
    if normalized == "users":
        return "users"

    # Common numeric naming conventions.
    if normalized.endswith("_ms"):
        return "ms"
    if normalized.endswith("_mb"):
        return "MB"
    if normalized.endswith("_gb"):
        return "GB"
    if normalized.endswith("_gib"):
        return "GiB"
    if normalized.endswith("_gb_month"):
        return "GB-month"
    if normalized.endswith("_months"):
        return "months"
    if normalized.endswith("_month"):
        return "month"

    # Derived totals naming conventions.
    suffixes = (
        ("_per_user_per_month", "user/month"),
        ("_per_month", "month"),
        ("_per_second", "second"),
    )
    for suffix, unit_tail in suffixes:
        if normalized.endswith(suffix):
            base = normalized[: -len(suffix)].strip("_")
            base = base.replace("_", " ")
            if unit_tail == "user/month":
                return f"{base}/user/month"
            return f"{base}/{unit_tail}"

    return ""


def _static_reason(parameter: str) -> str:
    # Keep reasons short; this is a debug artifact.
    if parameter == "users":
        return "From project expected_users."
    if parameter == "stage":
        return "From project stage."
    if parameter == "documents_per_month":
        return "Resolved from requirements.file_uploads (files_per_month)."
    if parameter == "average_document_size_mb":
        return "Resolved from requirements.file_uploads (average_file_size)."
    if parameter == "retention_months":
        return "Default retention months (12)."
    if parameter == "notification_channel_count":
        return "Count of enabled notification channels from requirements."
    if parameter == "authentication_methods":
        return "Enabled authentication methods from requirements."
    if parameter == "ses_free_tier_active":
        return "1 when stage is MVP (else 0)."
    return "Resolved by StaticUsageValueResolver."


def _reason_for_derived_total(
    total_key: str, *, final_inputs: dict[str, Any], users: float | None
) -> str | None:
    if users is None:
        return None
    total_val = final_inputs.get(total_key)
    if not _is_number(total_val):
        return None

    for derived_total, per_user_key in _PER_USER_DERIVED_TOTALS:
        if derived_total != total_key:
            continue
        per_user_val = final_inputs.get(per_user_key)
        if not _is_number(per_user_val):
            continue
        expected = users * float(per_user_val)
        if abs(float(total_val) - expected) < 1e-6:
            return f"Derived monthly total: users × {per_user_key}."
    return None


def _build_row(
    *,
    parameter: str,
    value: Any,
    source: str,
    reason: str,
    unit: str,
    used_by: list[str],
    status: str,
) -> dict[str, str]:
    return {
        "parameter": parameter,
        "value": _to_csv_cell(value),
        "unit": unit,
        "source": source,
        "reason": reason,
        "used_by": ";".join(used_by),
        "status": status,
    }


def build_usage_model_debug_csv(
    payload: GlobalUsageModelPayload,
    *,
    used_by: dict[str, list[str]] | None = None,
) -> str:
    used_by = used_by or {}

    final_inputs = build_usage_inputs(payload)

    users_raw = final_inputs.get("users")
    users: float | None = float(users_raw) if _is_number(users_raw) else None

    auth_methods = final_inputs.get("authentication_methods")
    sms_enabled = isinstance(auth_methods, list) and "sms" in auth_methods

    sms_llm_value: Any | None = None
    if sms_enabled and "sms_verifications_per_user_per_month" in payload.llm:
        sms_llm_value = payload.llm["sms_verifications_per_user_per_month"].value

    # Use deterministic ordering for easier diffs between runs.
    parameters = sorted(set(final_inputs.keys()) | set(payload.static.keys()) | set(payload.llm.keys()))

    rows: list[dict[str, str]] = []
    for parameter in parameters:
        source = ""
        reason = ""
        status = ""

        if parameter in payload.static:
            source = "static"
            reason = _static_reason(parameter)
            status = "resolved"
        elif parameter in payload.llm:
            source = "llm"
            llm_estimate = payload.llm[parameter]
            reason = llm_estimate.reason

            if (
                sms_enabled
                and parameter == "sms_verifications_per_user_per_month"
                and _is_number(final_inputs.get(parameter))
                and _is_number(sms_llm_value)
                and float(sms_llm_value) <= 0
                and float(final_inputs.get(parameter)) == _DERIVED_SMS_DEFAULT_VERIFICATIONS_PER_USER_PER_MONTH
            ):
                source = "derived"
                reason = "SMS enabled; defaulted verifications/user/month to 1.0."
                status = "defaulted"
            else:
                status = (
                    "defaulted"
                    if "Not applicable for capacity_mode" in reason
                    else "validated"
                )
        else:
            source = "derived"
            status = "derived"

            if parameter == "sms_verifications_per_user_per_month" and sms_enabled:
                if (
                    _is_number(final_inputs.get(parameter))
                    and float(final_inputs.get(parameter))
                    == _DERIVED_SMS_DEFAULT_VERIFICATIONS_PER_USER_PER_MONTH
                ):
                    reason = "SMS enabled; defaulted verifications/user/month to 1.0."
                    status = "defaulted"
                else:
                    reason = "SMS-enabled derived verifications/user/month."
            else:
                reason = (
                    _reason_for_derived_total(
                        parameter, final_inputs=final_inputs, users=users
                    )
                    or "Derived by build_usage_inputs()."
                )

        unit = _infer_unit(parameter)
        row = _build_row(
            parameter=parameter,
            value=final_inputs.get(parameter),
            source=source,
            reason=reason,
            unit=unit,
            used_by=used_by.get(parameter, []),
            status=status,
        )
        rows.append(row)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "parameter",
            "value",
            "unit",
            "source",
            "reason",
            "used_by",
            "status",
        ],
        extrasaction="ignore",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()

