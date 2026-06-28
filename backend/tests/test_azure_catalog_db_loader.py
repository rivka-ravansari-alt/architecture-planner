"""Tests for collecting Azure catalog services from the component catalog DB."""

from __future__ import annotations

from app.repositories.component_catalog_repository import ComponentCatalogRepository


def test_collect_azure_catalog_services_reads_from_db(db_session):
    repo = ComponentCatalogRepository(db_session)
    services = repo.collect_azure_catalog_services()
    names = {service.name for service in services}

    assert "Functions" in names
    assert "Blob Storage" in names
    assert "Queue Storage" in names
    assert "Azure App Service" in names

    blob = next(service for service in services if service.name == "Blob Storage")
    assert blob.api_service_name == "Storage"
    assert blob.price_filter == "contains(productName, 'Blob')"
