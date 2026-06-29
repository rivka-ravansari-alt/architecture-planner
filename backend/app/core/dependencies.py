"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.clients.ai_client import AIClientFactory, BaseAIClient
from app.clients.google_oauth_client import GoogleOAuthClient
from app.config.params import (
    ERR_INVALID_SESSION,
    ERR_NOT_AUTHENTICATED,
    ERR_USER_NOT_FOUND,
    PRICING_PROVIDER_AWS,
    PRICING_PROVIDER_AZURE,
    PRICING_PROVIDER_GCP,
)
from app.config.settings import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.models import User
from app.repositories.component_catalog_repository import ComponentCatalogRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.catalog_service import CatalogService
from app.services.cloud_defaults_service import CloudDefaultsService
from app.api.controllers.admin_pricing_controller import AdminPricingController
from app.pricing_ingestion.clients.aws_billing_client import AwsBillingClient
from app.pricing_ingestion.clients.azure_billing_client import AzureBillingClient
from app.pricing_ingestion.clients.gcp_billing_client import GcpBillingClient
from app.pricing_ingestion.providers.registry import PricingSyncRegistry
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.services.aws_pricing_sync_service import AwsPricingSyncService
from app.pricing_ingestion.services.azure_pricing_sync_service import AzurePricingSyncService
from app.pricing_ingestion.services.db_aws_catalog_loader import DbAwsCatalogLoader
from app.pricing_ingestion.services.db_azure_catalog_loader import DbAzureCatalogLoader
from app.pricing_ingestion.services.firestore_gcp_catalog_loader import FirestoreGcpCatalogLoader
from app.pricing_ingestion.services.gcp_pricing_sync_service import GcpPricingSyncService
from app.pricing_ingestion.services.pricing_sync_orchestrator import PricingSyncOrchestrator
from app.services.generation_service import GenerationService
from app.services.pricing_sync_auth import resolve_pricing_sync_principal
from app.services.project_service import ProjectService
from app.utils.jwt import JwtService


def get_jwt_service() -> JwtService:
    return JwtService()


def get_ai_client() -> BaseAIClient:
    return AIClientFactory.create()


@lru_cache
def get_google_oauth_client() -> GoogleOAuthClient:
    return GoogleOAuthClient()


def get_auth_service(
    db: Session = Depends(get_db),
    oauth_client: GoogleOAuthClient = Depends(get_google_oauth_client),
) -> AuthService:
    return AuthService(db, oauth_client=oauth_client)


def get_component_catalog_repository(
    db: Session = Depends(get_db),
) -> ComponentCatalogRepository:
    return ComponentCatalogRepository(db)


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def get_cloud_defaults_service(
    catalog_repo: ComponentCatalogRepository = Depends(get_component_catalog_repository),
) -> CloudDefaultsService:
    return CloudDefaultsService(catalog_repo)


def get_project_service(
    db: Session = Depends(get_db),
    catalog_service: CatalogService = Depends(get_catalog_service),
    cloud_defaults: CloudDefaultsService = Depends(get_cloud_defaults_service),
) -> ProjectService:
    return ProjectService(db, catalog_service=catalog_service, cloud_defaults=cloud_defaults)


def get_generation_service(
    db: Session = Depends(get_db),
    ai_client: BaseAIClient = Depends(get_ai_client),
    catalog_service: CatalogService = Depends(get_catalog_service),
    cloud_defaults: CloudDefaultsService = Depends(get_cloud_defaults_service),
) -> GenerationService:
    return GenerationService(
        db,
        ai_client=ai_client,
        catalog_service=catalog_service,
        cloud_defaults=cloud_defaults,
    )


def get_pricing_sync_registry(db: Session = Depends(get_db)) -> PricingSyncRegistry:
    firestore_client = FirestoreClientFactory.create()
    import_runs_repo = PriceImportRunsRepository(firestore_client)
    gcp_catalog_repo = GcpCatalogRepository(firestore_client)
    azure_catalog_repo = AzureCatalogRepository(firestore_client)
    component_catalog_repo = ComponentCatalogRepository(db)

    return PricingSyncRegistry(
        {
            PRICING_PROVIDER_GCP: GcpPricingSyncService(
                billing_client=GcpBillingClient(),
                catalog_repo=gcp_catalog_repo,
                import_runs_repo=import_runs_repo,
                service_loader=FirestoreGcpCatalogLoader(gcp_catalog_repo),
            ),
            PRICING_PROVIDER_AWS: AwsPricingSyncService(
                billing_client=AwsBillingClient(),
                catalog_repo=AwsCatalogRepository(firestore_client),
                import_runs_repo=import_runs_repo,
                service_loader=DbAwsCatalogLoader(component_catalog_repo),
            ),
            PRICING_PROVIDER_AZURE: AzurePricingSyncService(
                billing_client=AzureBillingClient(),
                catalog_repo=azure_catalog_repo,
                import_runs_repo=import_runs_repo,
                service_loader=DbAzureCatalogLoader(component_catalog_repo),
            ),
        }
    )


def get_pricing_sync_orchestrator(
    registry: PricingSyncRegistry = Depends(get_pricing_sync_registry),
) -> PricingSyncOrchestrator:
    return PricingSyncOrchestrator(registry)


def get_admin_pricing_controller(
    orchestrator: PricingSyncOrchestrator = Depends(get_pricing_sync_orchestrator),
) -> AdminPricingController:
    return AdminPricingController(orchestrator)


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    jwt_service: JwtService = Depends(get_jwt_service),
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None

    user_id = jwt_service.decode_access_token(token)
    if not user_id:
        return None

    return UserRepository(db).find_by_id(user_id)


def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    if user is None:
        raise UnauthorizedError(ERR_NOT_AUTHENTICATED)
    return user


def get_pricing_sync_principal(
    request: Request,
    user: User | None = Depends(get_optional_user),
) -> str:
    principal = resolve_pricing_sync_principal(request, user_id=user.id if user else None)
    if principal is None:
        raise UnauthorizedError(ERR_NOT_AUTHENTICATED)
    return principal
