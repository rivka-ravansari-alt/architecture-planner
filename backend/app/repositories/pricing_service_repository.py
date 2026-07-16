"""Pricing service persistence (Firestore ``pricing_services`` collection)."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.config.params import FIRESTORE_PRICING_SERVICES_COLLECTION


class PricingServiceRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._collection = client.collection(FIRESTORE_PRICING_SERVICES_COLLECTION)

    def upsert(self, service_id: str, document: dict[str, Any]) -> bool:
        """Create or update a pricing service and return True when newly created.

        The document id is the ``service_id`` so re-running never produces
        duplicates and never removes documents absent from the input.
        """

        reference = self._collection.document(service_id)
        existed = reference.get().exists
        payload = dict(document)
        payload["service_id"] = service_id
        reference.set(payload, merge=True)
        return not existed

    def find_by_id(self, service_id: str) -> dict[str, Any] | None:
        """Return a single pricing service document (with its id) or ``None``."""

        snapshot = self._collection.document(service_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["service_id"] = snapshot.id
        return data

    def list_all(self) -> list[dict[str, Any]]:
        """Return every pricing service document."""

        services: list[dict[str, Any]] = []
        for snapshot in self._collection.stream():
            data = snapshot.to_dict() or {}
            data["service_id"] = snapshot.id
            services.append(data)
        services.sort(key=lambda service: service.get("service_id", ""))
        return services
