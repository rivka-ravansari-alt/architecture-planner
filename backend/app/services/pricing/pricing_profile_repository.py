"""Firestore repository for data-driven component pricing profiles."""

from __future__ import annotations

import logging
from typing import Any

from app.config.params import FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES
from app.services.pricing.component_profiles import (
    COMPONENT_TYPE_ALIASES,
    ComponentProfile,
    profile_document_id,
    profile_from_firestore_document,
)
from app.utils.slug import slugify

logger = logging.getLogger(__name__)


class PricingProfileRepository:
    """Load component pricing profiles from Firestore.

    Profiles are selected by provider + component_type + cloud_service/service_slug.
    Provider and cloud_service may be "*" in Firestore to represent a controlled
    wildcard profile.
    """

    def __init__(self, client: Any, *, collection: str | None = None) -> None:
        self._client = client
        self._collection = collection or FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES

    def upsert(self, profile_doc: dict[str, Any]) -> str:
        doc_id = str(profile_doc.get("id") or profile_document_id(
            str(profile_doc.get("provider", "*")),
            str(profile_doc.get("component_type", "")),
            str(profile_doc.get("cloud_service", "*")),
        ))
        payload = {**profile_doc, "id": doc_id, "enabled": profile_doc.get("enabled", True)}
        self._client.collection(self._collection).document(doc_id).set(payload, merge=True)
        return doc_id

    def get_profile(
        self,
        *,
        provider: str,
        component_type: str,
        cloud_service: str,
    ) -> ComponentProfile | None:
        data = self.get_profile_document(
            provider=provider,
            component_type=component_type,
            cloud_service=cloud_service,
        )
        if data is None:
            return None
        try:
            return profile_from_firestore_document(data)
        except ValueError as exc:
            logger.warning("Invalid pricing profile document id=%s error=%s", data.get("id"), exc)
            return None

    def get_profile_document(
        self,
        *,
        provider: str,
        component_type: str,
        cloud_service: str,
    ) -> dict[str, Any] | None:
        provider_key = provider.casefold()
        normalized_type = COMPONENT_TYPE_ALIASES.get(component_type, component_type)
        service_slug = slugify(cloud_service)

        best: tuple[int, dict[str, Any]] | None = None
        for snapshot in self._client.collection(self._collection).stream():
            data = snapshot.to_dict() or {}
            if not self._matches(data, provider_key, normalized_type, service_slug):
                continue
            score = self._score(data, provider_key, service_slug)
            if best is None or score > best[0]:
                best = (score, data)
        return best[1] if best is not None else None

    def _get_doc(self, doc_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection(self._collection).document(doc_id).get()
        if not getattr(snapshot, "exists", False):
            return None
        data = snapshot.to_dict() or {}
        if data.get("enabled") is False:
            return None
        return data

    @staticmethod
    def _matches(
        data: dict[str, Any],
        provider_key: str,
        component_type: str,
        service_slug: str,
    ) -> bool:
        if data.get("enabled") is False:
            return False
        doc_provider = str(data.get("provider", "*")).casefold()
        if doc_provider not in {provider_key, "*"}:
            return False

        doc_type = COMPONENT_TYPE_ALIASES.get(
            str(data.get("component_type", "")),
            str(data.get("component_type", "")),
        )
        if doc_type not in {component_type, "*"}:
            return False

        doc_slug = str(data.get("service_slug") or slugify(str(data.get("cloud_service", "*"))))
        if doc_slug in {service_slug, "*"}:
            return True

        aliases = {str(item) for item in data.get("service_alias_slugs", [])}
        aliases.update(slugify(str(item)) for item in data.get("service_aliases", []))
        return service_slug in aliases

    @staticmethod
    def _score(data: dict[str, Any], provider_key: str, service_slug: str) -> int:
        score = 0
        if str(data.get("provider", "*")).casefold() == provider_key:
            score += 200
        if str(data.get("component_type", "")) != "*":
            score += 20
        doc_slug = str(data.get("service_slug") or slugify(str(data.get("cloud_service", "*"))))
        if doc_slug == service_slug:
            score += 100
        elif service_slug in {str(item) for item in data.get("service_alias_slugs", [])}:
            score += 80
        elif doc_slug == "*":
            score += 1
        return score
