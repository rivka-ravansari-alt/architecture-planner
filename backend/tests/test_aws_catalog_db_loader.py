"""Tests for collecting AWS catalog services from the component catalog DB."""

from __future__ import annotations

from app.repositories.component_catalog_repository import ComponentCatalogRepository


def test_collect_aws_catalog_services_reads_from_db(db_session):
    repo = ComponentCatalogRepository(db_session)
    services = repo.collect_aws_catalog_services()
    names = {service.name for service in services}

    assert "Lambda" in names
    assert "S3" in names
    assert "ECS Fargate" in names

    lambda_service = next(service for service in services if service.name == "Lambda")
    assert lambda_service.api_service_code == "AWSLambda"

    fargate = next(service for service in services if service.name == "ECS Fargate")
    assert fargate.api_service_code == "AmazonECS"
    assert fargate.attribute_filters
