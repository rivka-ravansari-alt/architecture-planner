"""Resolve architecture cloud options to Firestore pricing catalog documents."""

from __future__ import annotations

import logging
from typing import Any

from app.config.params import (
    AWS_CATALOG_SKIP_OPTIONS,
    AZURE_CATALOG_SKIP_OPTIONS,
    CLOUD_PROVIDERS,
    GCP_CATALOG_SKIP_OPTIONS,
)
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.base_catalog_repository import BaseCatalogRepository
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.utils.slug import slugify

logger = logging.getLogger(__name__)

SKIP_OPTIONS_BY_PROVIDER: dict[str, frozenset[str]] = {
    "gcp": GCP_CATALOG_SKIP_OPTIONS,
    "aws": AWS_CATALOG_SKIP_OPTIONS,
    "azure": AZURE_CATALOG_SKIP_OPTIONS,
}

# Alternate Firestore service names for weak slug matches.
CATALOG_LOOKUP_ALIASES: dict[tuple[str, str], tuple[str, ...]] = {
    ("aws", "Cognito"): ("Amazon Cognito", "Cognito"),
    ("gcp", "Firebase Authentication"): ("Identity Toolkit", "Firebase Authentication"),
    ("gcp", "Identity Platform"): ("Identity Platform", "Cloud Identity Platform"),
    ("azure", "Entra ID B2C"): (
        "Entra ID B2C",
        "Azure Active Directory B2C",
        "Microsoft Entra ID B2C",
    ),
}


class PricingCatalogLookup:
    def __init__(
        self,
        *,
        gcp_repo: BaseCatalogRepository | None = None,
        aws_repo: BaseCatalogRepository | None = None,
        azure_repo: BaseCatalogRepository | None = None,
    ) -> None:
        self._repos: dict[str, BaseCatalogRepository] = {}
        if gcp_repo is not None:
            self._repos["gcp"] = gcp_repo
        if aws_repo is not None:
            self._repos["aws"] = aws_repo
        if azure_repo is not None:
            self._repos["azure"] = azure_repo

    @classmethod
    def from_firestore_client(cls, client: Any) -> PricingCatalogLookup:
        return cls(
            gcp_repo=GcpCatalogRepository(client),
            aws_repo=AwsCatalogRepository(client),
            azure_repo=AzureCatalogRepository(client),
        )

    def pick_cloud_option(self, provider: str, options: list[str]) -> str | None:
        skip = SKIP_OPTIONS_BY_PROVIDER.get(provider, frozenset())
        for option in options:
            cleaned = str(option).strip()
            if not cleaned or cleaned in skip:
                continue
            return cleaned
        return None

    def lookup(self, provider: str, option_name: str) -> dict[str, Any] | None:
        if provider not in CLOUD_PROVIDERS:
            return None
        repo = self._repos.get(provider)
        if repo is None:
            return None

        try:
            for candidate_name in self._candidate_names(provider, option_name):
                doc = repo.get(slugify(candidate_name))
                if self._is_priced(doc):
                    return doc

            for candidate_name in self._candidate_names(provider, option_name):
                lowered = candidate_name.casefold()
                for service_name in repo.list_enabled_service_names():
                    if self._matches_service(lowered, service_name.casefold()):
                        doc = repo.get(slugify(service_name))
                        if self._is_priced(doc):
                            return doc
        except Exception as exc:
            logger.warning(
                "catalog_lookup failed provider=%s option=%s error=%s",
                provider,
                option_name,
                exc,
            )
            return None

        return None

    def _candidate_names(self, provider: str, option_name: str) -> list[str]:
        names = [option_name]
        aliases = CATALOG_LOOKUP_ALIASES.get((provider, option_name), ())
        for alias in aliases:
            if alias not in names:
                names.append(alias)
        return names

    @staticmethod
    def _matches_service(option_lower: str, service_lower: str) -> bool:
        if option_lower == service_lower:
            return True
        if "firebase authentication" in option_lower and service_lower == "firebase":
            return False
        if "identity platform" in option_lower and service_lower == "firebase":
            return False
        if any(token in option_lower for token in ("authentication", "identity", "entra", "cognito")):
            if not any(
                token in service_lower
                for token in ("auth", "identity", "cognito", "entra", "active directory")
            ):
                return False
        if option_lower in service_lower:
            return True
        return service_lower in option_lower and len(service_lower) >= len(option_lower) * 0.6

    @staticmethod
    def _is_priced(doc: dict[str, Any] | None) -> bool:
        if not doc:
            return False
        skus = doc.get("skus")
        return isinstance(skus, dict) and len(skus) > 0
