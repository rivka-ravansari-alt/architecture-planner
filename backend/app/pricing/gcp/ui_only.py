"""GCP UI-only services with no standalone metered catalog pricing."""

from __future__ import annotations

from app.pricing.gcp.registry import normalize_gcp_service_name

LOOKER_STUDIO_UI_ONLY_NOTE = (
    "Looker Studio itself has no significant standalone metered cost. "
    "Analytics costs are billed through the connected data source (e.g. BigQuery)."
)

GCP_UI_ONLY_SERVICES: frozenset[str] = frozenset({"Looker Studio"})

GCP_UI_ONLY_NOTES: dict[str, str] = {
    "Looker Studio": LOOKER_STUDIO_UI_ONLY_NOTE,
}


def is_gcp_ui_only_service(service_name: str) -> bool:
    """Return True when the mapped service is priced via backing services, not catalog SKUs."""
    stripped = service_name.strip()
    if not stripped:
        return False
    canonical = normalize_gcp_service_name(stripped)
    return (
        stripped in GCP_UI_ONLY_SERVICES
        or canonical in GCP_UI_ONLY_SERVICES
        or stripped.casefold() in {name.casefold() for name in GCP_UI_ONLY_SERVICES}
    )


def ui_only_note_for_service(service_name: str) -> str:
    """Human-readable explanation for a UI-only GCP service selection."""
    stripped = service_name.strip()
    if stripped in GCP_UI_ONLY_NOTES:
        return GCP_UI_ONLY_NOTES[stripped]
    canonical = normalize_gcp_service_name(stripped)
    return GCP_UI_ONLY_NOTES.get(canonical, LOOKER_STUDIO_UI_ONLY_NOTE)
