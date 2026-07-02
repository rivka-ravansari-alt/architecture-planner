"""Component pricing profiles — roles, constraints, formulas (no SKU IDs)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.utils.slug import slugify


class PricingRole(str, Enum):
    """Semantic billing roles. Firestore SKUs are classified into these at runtime."""

    CPU = "cpu"
    MEMORY = "memory"
    REQUESTS = "requests"
    EGRESS = "egress"
    GB_SECONDS = "gb_seconds"
    EXECUTION = "execution"
    STORAGE = "storage"
    READ_OPERATIONS = "read_operations"
    WRITE_OPERATIONS = "write_operations"
    INSTANCE = "instance"
    CACHE_INSTANCE = "cache_instance"
    GATEWAY_CAPACITY = "gateway_capacity"
    MAU = "monthly_active_users"
    AUTH_EVENTS = "auth_events"
    SMS_MFA = "sms_mfa"
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    INFERENCE = "inference"
    HOSTING = "hosting"
    COMPUTE = "compute"
    DATA_TRANSFER = "data_transfer"
    QUEUE_MESSAGES = "queue_messages"
    LOG_INGESTION = "log_ingestion"
    BACKUP = "backup"


class FormulaKind(str, Enum):
    """How selected SKUs combine into a monthly cost expression."""

    CLOUD_RUN = "cloud_run"
    LAMBDA = "lambda"
    AZURE_FUNCTIONS = "azure_functions"
    ECS_FARGATE = "ecs_fargate"
    CONTAINER_APPS = "container_apps"
    REQUESTS_ONLY = "requests_only"
    GATEWAY = "gateway"
    OBJECT_STORAGE = "object_storage"
    DATABASE = "database"
    DATABASE_NOSQL = "database_nosql"
    CACHE = "cache"
    AUTH = "auth"
    AI = "ai"
    CDN = "cdn"
    HOSTING = "hosting"
    QUEUE = "queue"
    MONITORING = "monitoring"
    LOAD_BALANCER = "load_balancer"
    GENERIC = "generic"


# Shared SKU haystack patterns rejected for specific component families.
REJECT_DB = ("export", "import", "restore", "migration", "backup restore", "snapshot export")
REJECT_STORAGE = ("cdn", "cache-fill", "cache fill", "origin shield")
REJECT_HOSTING = ("front door", "frontdoor", "cdn", "network egress", "add-on", "addon")
REJECT_COMPUTE_NETWORK = ("egress", "network internet", "data transfer", "interregion", "peering")


@dataclass(frozen=True)
class ComponentProfile:
    """Pricing model: required/optional/forbidden roles, SKU reject rules, formula."""

    name: str
    required_roles: frozenset[PricingRole]
    optional_roles: frozenset[PricingRole] = field(default_factory=frozenset)
    forbidden_roles: frozenset[PricingRole] = field(default_factory=frozenset)
    mutually_exclusive: tuple[frozenset[PricingRole], ...] = ()
    sku_reject_patterns: tuple[str, ...] = ()
    role_reject_patterns: tuple[tuple[PricingRole, tuple[str, ...]], ...] = ()
    formula: FormulaKind = FormulaKind.GENERIC
    description: str = ""
    default_tier_by_stage: dict[str, int] = field(default_factory=dict)
    usage_mapping: dict[str, str] = field(default_factory=dict)
    quantity_mapping: dict[str, str] = field(default_factory=dict)
    confidence_rules: dict[str, Any] = field(default_factory=dict)
    expected_monthly_ranges: dict[str, dict[str, float]] = field(default_factory=dict)

    def all_roles(self) -> frozenset[PricingRole]:
        return self.required_roles | self.optional_roles

    def allows(self, role: PricingRole) -> bool:
        return role in self.all_roles() and role not in self.forbidden_roles

    def is_required(self, role: PricingRole) -> bool:
        return role in self.required_roles

    def is_forbidden(self, role: PricingRole) -> bool:
        return role in self.forbidden_roles

    def exclusive_group_for(self, role: PricingRole) -> frozenset[PricingRole] | None:
        for group in self.mutually_exclusive:
            if role in group:
                return group
        return None

    def reject_patterns_for(self, role: PricingRole) -> tuple[str, ...]:
        extra = next((patterns for r, patterns in self.role_reject_patterns if r == role), ())
        return self.sku_reject_patterns + extra


@dataclass(frozen=True)
class ProfileResolution:
    profile: ComponentProfile | None
    missing_data: list[str] = field(default_factory=list)
    source: str = "firestore"
    used_fallback: bool = False


EXPECTED_MONTHLY_RANGES: dict[str, dict[str, dict[str, float]]] = {
    "cloud_run": {
        "mvp_100": {"min": 0.0, "max": 15.0},
        "mvp_1000": {"min": 0.5, "max": 75.0},
        "production_10000": {"min": 20.0, "max": 500.0},
    },
    "lambda": {
        "mvp_100": {"min": 0.01, "max": 20.0},
        "mvp_1000": {"min": 0.1, "max": 100.0},
        "production_10000": {"min": 5.0, "max": 500.0},
    },
    "azure_functions": {
        "mvp_100": {"min": 0.01, "max": 20.0},
        "mvp_1000": {"min": 0.1, "max": 100.0},
        "production_10000": {"min": 5.0, "max": 500.0},
    },
    "container_apps": {
        "mvp_100": {"min": 0.5, "max": 50.0},
        "mvp_1000": {"min": 5.0, "max": 200.0},
        "production_10000": {"min": 30.0, "max": 1000.0},
    },
    "ecs_fargate": {
        "mvp_100": {"min": 1.0, "max": 80.0},
        "mvp_1000": {"min": 10.0, "max": 300.0},
        "production_10000": {"min": 50.0, "max": 1500.0},
    },
    "api_gateway": {
        "mvp_100": {"min": 0.0, "max": 25.0},
        "mvp_1000": {"min": 0.0, "max": 100.0},
        "production_10000": {"min": 1.0, "max": 500.0},
    },
    "api_management": {
        "mvp_100": {"min": 0.0, "max": 150.0},
        "mvp_1000": {"min": 0.0, "max": 500.0},
        "production_10000": {"min": 10.0, "max": 2000.0},
    },
    "object_storage": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 1.0, "max": 500.0},
        "production_10000": {"min": 25.0, "max": 5000.0},
    },
    "database_sql": {
        "mvp_100": {"min": 5.0, "max": 300.0},
        "mvp_1000": {"min": 30.0, "max": 1000.0},
        "production_10000": {"min": 250.0, "max": 5000.0},
    },
    "database_nosql": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 1.0, "max": 300.0},
        "production_10000": {"min": 10.0, "max": 1000.0},
    },
    "cache": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 10.0, "max": 300.0},
        "production_10000": {"min": 50.0, "max": 1500.0},
    },
    "auth": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 0.0, "max": 200.0},
        "production_10000": {"min": 0.0, "max": 1000.0},
    },
    "ai": {
        "mvp_100": {"min": 0.0, "max": 500.0},
        "mvp_1000": {"min": 10.0, "max": 2000.0},
        "production_10000": {"min": 100.0, "max": 15000.0},
    },
    "cdn": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 1.0, "max": 500.0},
        "production_10000": {"min": 20.0, "max": 3000.0},
    },
    "web_app": {
        "mvp_100": {"min": 0.0, "max": 50.0},
        "mvp_1000": {"min": 0.0, "max": 200.0},
        "production_10000": {"min": 10.0, "max": 1000.0},
    },
    "queue": {
        "mvp_100": {"min": 0.0, "max": 50.0},
        "mvp_1000": {"min": 0.0, "max": 100.0},
        "production_10000": {"min": 1.0, "max": 500.0},
    },
    "monitoring": {
        "mvp_100": {"min": 0.0, "max": 50.0},
        "mvp_1000": {"min": 0.0, "max": 200.0},
        "production_10000": {"min": 10.0, "max": 1000.0},
    },
    "load_balancer": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 0.0, "max": 300.0},
        "production_10000": {"min": 10.0, "max": 1500.0},
    },
    "generic": {
        "mvp_100": {"min": 0.0, "max": 100.0},
        "mvp_1000": {"min": 0.0, "max": 300.0},
        "production_10000": {"min": 10.0, "max": 1000.0},
    },
}


def _expected_ranges(profile_name: str) -> dict[str, dict[str, float]]:
    return dict(EXPECTED_MONTHLY_RANGES.get(profile_name, EXPECTED_MONTHLY_RANGES["generic"]))


def _profile(
    name: str,
    *,
    required: tuple[PricingRole, ...],
    optional: tuple[PricingRole, ...] = (),
    forbidden: tuple[PricingRole, ...] = (),
    mutually_exclusive: tuple[frozenset[PricingRole], ...] = (),
    sku_reject_patterns: tuple[str, ...] = (),
    role_reject_patterns: tuple[tuple[PricingRole, tuple[str, ...]], ...] = (),
    formula: FormulaKind,
    description: str = "",
    default_tier_by_stage: dict[str, int] | None = None,
    usage_mapping: dict[str, str] | None = None,
    quantity_mapping: dict[str, str] | None = None,
    confidence_rules: dict[str, Any] | None = None,
    expected_monthly_ranges: dict[str, dict[str, float]] | None = None,
) -> ComponentProfile:
    return ComponentProfile(
        name=name,
        required_roles=frozenset(required),
        optional_roles=frozenset(optional),
        forbidden_roles=frozenset(forbidden),
        mutually_exclusive=mutually_exclusive,
        sku_reject_patterns=sku_reject_patterns,
        role_reject_patterns=role_reject_patterns,
        formula=formula,
        description=description,
        default_tier_by_stage=default_tier_by_stage or {},
        usage_mapping=usage_mapping or {},
        quantity_mapping=quantity_mapping or {},
        confidence_rules=confidence_rules or {},
        expected_monthly_ranges=expected_monthly_ranges or _expected_ranges(name),
    )


PROFILE_CLOUD_RUN = _profile(
    "cloud_run",
    required=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.REQUESTS),
    optional=(PricingRole.EGRESS,),
    forbidden=(PricingRole.GATEWAY_CAPACITY, PricingRole.HOSTING, PricingRole.STORAGE),
    role_reject_patterns=(
        (PricingRole.CPU, REJECT_COMPUTE_NETWORK),
        (PricingRole.MEMORY, REJECT_COMPUTE_NETWORK),
    ),
    formula=FormulaKind.CLOUD_RUN,
)

PROFILE_LAMBDA = _profile(
    "lambda",
    required=(PricingRole.REQUESTS, PricingRole.GB_SECONDS),
    optional=(PricingRole.EGRESS,),
    forbidden=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.GATEWAY_CAPACITY),
    role_reject_patterns=((PricingRole.GB_SECONDS, ("streaming", "processed-gigabyte", "network")),),
    mutually_exclusive=(frozenset({PricingRole.GB_SECONDS, PricingRole.EXECUTION}),),
    formula=FormulaKind.LAMBDA,
)

PROFILE_AZURE_FUNCTIONS = _profile(
    "azure_functions",
    required=(PricingRole.EXECUTION,),
    optional=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.REQUESTS, PricingRole.EGRESS),
    forbidden=(PricingRole.GB_SECONDS, PricingRole.GATEWAY_CAPACITY),
    formula=FormulaKind.AZURE_FUNCTIONS,
)

PROFILE_CONTAINER_APPS = _profile(
    "container_apps",
    required=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.REQUESTS),
    optional=(PricingRole.EGRESS,),
    forbidden=(PricingRole.GATEWAY_CAPACITY,),
    role_reject_patterns=(
        (PricingRole.CPU, REJECT_COMPUTE_NETWORK),
        (PricingRole.MEMORY, REJECT_COMPUTE_NETWORK),
    ),
    formula=FormulaKind.CONTAINER_APPS,
)

PROFILE_ECS_FARGATE = _profile(
    "ecs_fargate",
    required=(PricingRole.CPU, PricingRole.MEMORY),
    optional=(PricingRole.REQUESTS, PricingRole.EGRESS),
    forbidden=(PricingRole.GB_SECONDS, PricingRole.GATEWAY_CAPACITY),
    role_reject_patterns=(
        (PricingRole.CPU, REJECT_COMPUTE_NETWORK),
        (PricingRole.MEMORY, REJECT_COMPUTE_NETWORK),
    ),
    formula=FormulaKind.ECS_FARGATE,
)

PROFILE_API_GATEWAY = _profile(
    "api_gateway",
    required=(PricingRole.REQUESTS,),
    optional=(PricingRole.DATA_TRANSFER,),
    forbidden=(
        PricingRole.CPU,
        PricingRole.MEMORY,
        PricingRole.STORAGE,
        PricingRole.INSTANCE,
        PricingRole.EGRESS,
    ),
    sku_reject_patterns=REJECT_COMPUTE_NETWORK,
    formula=FormulaKind.REQUESTS_ONLY,
)

PROFILE_API_MANAGEMENT = _profile(
    "api_management",
    required=(PricingRole.REQUESTS,),
    optional=(PricingRole.GATEWAY_CAPACITY, PricingRole.DATA_TRANSFER),
    forbidden=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.STORAGE, PricingRole.EGRESS),
    mutually_exclusive=(frozenset({PricingRole.REQUESTS, PricingRole.GATEWAY_CAPACITY}),),
    formula=FormulaKind.GATEWAY,
)

PROFILE_OBJECT_STORAGE = _profile(
    "object_storage",
    required=(PricingRole.STORAGE, PricingRole.READ_OPERATIONS, PricingRole.WRITE_OPERATIONS),
    optional=(PricingRole.EGRESS,),
    forbidden=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.INSTANCE, PricingRole.CACHE_INSTANCE),
    sku_reject_patterns=REJECT_STORAGE,
    formula=FormulaKind.OBJECT_STORAGE,
)

PROFILE_DATABASE_SQL = _profile(
    "database_sql",
    required=(
        PricingRole.INSTANCE,
        PricingRole.STORAGE,
        PricingRole.READ_OPERATIONS,
        PricingRole.WRITE_OPERATIONS,
    ),
    optional=(PricingRole.BACKUP,),
    forbidden=(PricingRole.EGRESS, PricingRole.CPU, PricingRole.REQUESTS, PricingRole.CACHE_INSTANCE),
    sku_reject_patterns=REJECT_DB,
    formula=FormulaKind.DATABASE,
)

PROFILE_DATABASE_NOSQL = _profile(
    "database_nosql",
    required=(PricingRole.READ_OPERATIONS, PricingRole.WRITE_OPERATIONS, PricingRole.STORAGE),
    optional=(PricingRole.BACKUP,),
    forbidden=(PricingRole.INSTANCE, PricingRole.EGRESS, PricingRole.CPU, PricingRole.CACHE_INSTANCE),
    sku_reject_patterns=REJECT_DB,
    formula=FormulaKind.DATABASE_NOSQL,
)

PROFILE_CACHE = _profile(
    "cache",
    required=(PricingRole.CACHE_INSTANCE,),
    forbidden=(PricingRole.STORAGE, PricingRole.EGRESS, PricingRole.REQUESTS, PricingRole.READ_OPERATIONS),
    formula=FormulaKind.CACHE,
)

PROFILE_AUTH = _profile(
    "auth",
    required=(PricingRole.MAU, PricingRole.AUTH_EVENTS),
    optional=(PricingRole.SMS_MFA,),
    forbidden=(
        PricingRole.CPU,
        PricingRole.MEMORY,
        PricingRole.STORAGE,
        PricingRole.EGRESS,
        PricingRole.INSTANCE,
    ),
    mutually_exclusive=(frozenset({PricingRole.MAU, PricingRole.AUTH_EVENTS}),),
    formula=FormulaKind.AUTH,
)

PROFILE_AI = _profile(
    "ai",
    required=(PricingRole.INPUT_TOKENS, PricingRole.OUTPUT_TOKENS),
    optional=(PricingRole.REQUESTS, PricingRole.INFERENCE),
    forbidden=(PricingRole.CPU, PricingRole.MEMORY, PricingRole.STORAGE, PricingRole.INSTANCE),
    sku_reject_patterns=("commit", "training", "tuning", "hosting", "hour"),
    formula=FormulaKind.AI,
)

PROFILE_CDN = _profile(
    "cdn",
    required=(PricingRole.EGRESS,),
    optional=(PricingRole.REQUESTS,),
    forbidden=(PricingRole.STORAGE, PricingRole.INSTANCE, PricingRole.CPU, PricingRole.CACHE_INSTANCE),
    formula=FormulaKind.CDN,
)

PROFILE_WEB_APP = _profile(
    "web_app",
    required=(PricingRole.HOSTING, PricingRole.STORAGE, PricingRole.REQUESTS),
    optional=(PricingRole.COMPUTE, PricingRole.EGRESS),
    forbidden=(PricingRole.INSTANCE, PricingRole.CACHE_INSTANCE, PricingRole.GATEWAY_CAPACITY),
    sku_reject_patterns=REJECT_HOSTING,
    formula=FormulaKind.HOSTING,
)

PROFILE_QUEUE = _profile(
    "queue",
    required=(PricingRole.QUEUE_MESSAGES,),
    optional=(PricingRole.REQUESTS,),
    forbidden=(PricingRole.STORAGE, PricingRole.EGRESS, PricingRole.CPU, PricingRole.INSTANCE),
    sku_reject_patterns=("cloud storage", "gcs delivery"),
    mutually_exclusive=(frozenset({PricingRole.QUEUE_MESSAGES, PricingRole.REQUESTS}),),
    formula=FormulaKind.QUEUE,
)

PROFILE_MONITORING = _profile(
    "monitoring",
    required=(PricingRole.LOG_INGESTION,),
    optional=(PricingRole.REQUESTS,),
    forbidden=(PricingRole.STORAGE, PricingRole.EGRESS, PricingRole.INSTANCE),
    formula=FormulaKind.MONITORING,
)

PROFILE_LOAD_BALANCER = _profile(
    "load_balancer",
    required=(PricingRole.GATEWAY_CAPACITY,),
    optional=(PricingRole.EGRESS, PricingRole.REQUESTS),
    forbidden=(PricingRole.STORAGE, PricingRole.CACHE_INSTANCE),
    formula=FormulaKind.LOAD_BALANCER,
)

PROFILE_GENERIC = _profile(
    "generic",
    required=(PricingRole.REQUESTS,),
    optional=(PricingRole.STORAGE, PricingRole.EGRESS),
    forbidden=(PricingRole.INSTANCE, PricingRole.CACHE_INSTANCE),
    formula=FormulaKind.GENERIC,
)

COMPONENT_TYPE_ALIASES: dict[str, str] = {
    "api": "api_gateway",
    "service": "app_service",
    "worker": "queue_worker",
    "ai_service": "ai_provider",
    "authentication": "auth",
    "mobile_app": "web_app",
    "admin_panel": "web_app",
}

BASE_PROFILE_BY_TYPE: dict[str, ComponentProfile] = {
    "web_app": PROFILE_WEB_APP,
    "mobile_app": PROFILE_WEB_APP,
    "admin_panel": PROFILE_WEB_APP,
    "api_gateway": PROFILE_API_GATEWAY,
    "app_service": PROFILE_GENERIC,
    "queue_worker": PROFILE_CLOUD_RUN,
    "object_storage": PROFILE_OBJECT_STORAGE,
    "database": PROFILE_DATABASE_SQL,
    "cache": PROFILE_CACHE,
    "auth": PROFILE_AUTH,
    "cdn": PROFILE_CDN,
    "ai_provider": PROFILE_AI,
    "queue": PROFILE_QUEUE,
    "monitoring": PROFILE_MONITORING,
    "load_balancer": PROFILE_LOAD_BALANCER,
}

DEFAULT_USAGE_MAPPING: dict[str, str] = {
    "cpu": "monthly_vcpu_hours",
    "memory": "monthly_memory_gib_hours",
    "requests": "monthly_requests",
    "egress": "egress_gb",
    "data_transfer": "egress_gb",
    "storage": "storage_gib",
    "read_operations": "monthly_requests",
    "write_operations": "monthly_requests",
    "instance": "instance_billable_units",
    "cache_instance": "instance_billable_units",
    "gateway_capacity": "gateway_units",
    "gb_seconds": "monthly_gb_seconds",
    "execution": "monthly_executions",
    "monthly_active_users": "monthly_auth_events",
    "auth_events": "monthly_auth_events",
    "sms_mfa": "monthly_auth_events",
    "input_tokens": "monthly_tokens",
    "output_tokens": "monthly_tokens",
    "inference": "monthly_tokens",
    "hosting": "monthly_requests",
    "compute": "monthly_requests",
    "queue_messages": "monthly_requests",
    "log_ingestion": "log_ingestion_gb",
    "backup": "backup_gib",
}


PROFILE_SEED_TARGETS: tuple[tuple[ComponentProfile, str, str, tuple[str, ...]], ...] = (
    (PROFILE_CLOUD_RUN, "*", "Cloud Run", ("Google Cloud Run",)),
    (PROFILE_LAMBDA, "*", "Lambda", ("AWS Lambda",)),
    (PROFILE_AZURE_FUNCTIONS, "*", "Azure Functions", ("Functions",)),
    (PROFILE_CONTAINER_APPS, "*", "Container Apps", ("Azure Container Apps",)),
    (PROFILE_ECS_FARGATE, "*", "ECS Fargate", ("Fargate", "Amazon ECS")),
    (PROFILE_API_GATEWAY, "api_gateway", "*", ()),
    (PROFILE_API_MANAGEMENT, "api_gateway", "API Management", ("Azure API Management", "APIM")),
    (PROFILE_OBJECT_STORAGE, "object_storage", "*", ("S3", "Cloud Storage", "Blob Storage")),
    (PROFILE_DATABASE_SQL, "database", "*", ("RDS", "Cloud SQL", "Azure SQL", "PostgreSQL", "MySQL")),
    (
        PROFILE_DATABASE_NOSQL,
        "database",
        "Firestore",
        ("Cloud Firestore", "DynamoDB", "Azure Cosmos DB", "Cosmos DB", "Cosmos"),
    ),
    (PROFILE_CACHE, "cache", "*", ("ElastiCache", "Memorystore", "Azure Cache")),
    (PROFILE_AUTH, "auth", "*", ("Cognito", "Firebase Authentication", "Identity Platform", "Entra ID B2C")),
    (PROFILE_AI, "ai_provider", "*", ("Vertex AI", "Bedrock", "Azure OpenAI")),
    (PROFILE_CDN, "cdn", "*", ("CloudFront", "Cloud CDN", "Azure CDN")),
    (PROFILE_WEB_APP, "web_app", "*", ("Amplify Hosting", "Firebase Hosting", "Azure App Service")),
    (PROFILE_QUEUE, "queue", "*", ("SQS", "Pub/Sub", "Service Bus")),
    (PROFILE_MONITORING, "monitoring", "*", ("CloudWatch", "Cloud Monitoring", "Azure Monitor")),
    (PROFILE_LOAD_BALANCER, "load_balancer", "*", ("ELB", "Cloud Load Balancing", "Azure Load Balancer")),
)


def profile_document_id(provider: str, component_type: str, cloud_service: str) -> str:
    return "__".join(
        [
            provider.casefold() if provider else "*",
            COMPONENT_TYPE_ALIASES.get(component_type, component_type),
            "*" if cloud_service == "*" else slugify(cloud_service),
        ]
    )


def profile_to_firestore_document(
    profile: ComponentProfile,
    *,
    provider: str,
    component_type: str,
    cloud_service: str,
    service_aliases: tuple[str, ...] = (),
) -> dict[str, Any]:
    all_roles = profile.required_roles | profile.optional_roles
    usage_mapping = {
        role.value: DEFAULT_USAGE_MAPPING[role.value]
        for role in all_roles
        if role.value in DEFAULT_USAGE_MAPPING
    }
    service_slug = "*" if cloud_service == "*" else slugify(cloud_service)
    return {
        "id": profile_document_id(provider, component_type, cloud_service),
        "enabled": True,
        "provider": provider,
        "component_type": COMPONENT_TYPE_ALIASES.get(component_type, component_type),
        "cloud_service": cloud_service,
        "service_slug": service_slug,
        "service_aliases": list(service_aliases),
        "service_alias_slugs": [slugify(alias) for alias in service_aliases],
        "profile_key": profile.name,
        "required_roles": sorted(role.value for role in profile.required_roles),
        "optional_roles": sorted(role.value for role in profile.optional_roles),
        "forbidden_roles": sorted(role.value for role in profile.forbidden_roles),
        "forbidden_patterns": list(profile.sku_reject_patterns),
        "role_forbidden_patterns": {
            role.value: list(patterns) for role, patterns in profile.role_reject_patterns
        },
        "mutual_exclusion_groups": [
            {"roles": sorted(role.value for role in group)}
            for group in profile.mutually_exclusive
        ],
        "formula_kind": profile.formula.value,
        "default_tier_by_stage": profile.default_tier_by_stage
        or {"mvp": 2, "production": 4},
        "usage_mapping": profile.usage_mapping or usage_mapping,
        "quantity_mapping": profile.quantity_mapping,
        "confidence_rules": profile.confidence_rules
        or {
            "missing_required_role": "low",
            "missing_profile": "low",
            "fallback_profile": "low",
        },
        "expected_monthly_ranges": profile.expected_monthly_ranges,
        "description": profile.description,
    }


def iter_default_profile_documents() -> list[dict[str, Any]]:
    return [
        profile_to_firestore_document(
            profile,
            provider="*",
            component_type=component_type,
            cloud_service=cloud_service,
            service_aliases=aliases,
        )
        for profile, component_type, cloud_service, aliases in PROFILE_SEED_TARGETS
    ]


def profile_from_firestore_document(data: dict[str, Any]) -> ComponentProfile:
    try:
        formula = FormulaKind(str(data["formula_kind"]))
        required = _roles(data.get("required_roles", ()))
        optional = _roles(data.get("optional_roles", ()))
        forbidden = _roles(data.get("forbidden_roles", ()))
        mutually_exclusive = tuple(
            frozenset(_roles(group.get("roles", ())))
            for group in data.get("mutual_exclusion_groups", ())
            if isinstance(group, dict)
        )
        role_patterns = tuple(
            (PricingRole(str(role)), tuple(str(pattern) for pattern in patterns))
            for role, patterns in dict(data.get("role_forbidden_patterns", {})).items()
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid pricing component profile document: {exc}") from exc

    profile_name = str(data.get("profile_key") or data.get("name") or formula.value)
    expected_ranges = data.get("expected_monthly_ranges") or _expected_ranges(profile_name)

    return ComponentProfile(
        name=profile_name,
        required_roles=frozenset(required),
        optional_roles=frozenset(optional),
        forbidden_roles=frozenset(forbidden),
        mutually_exclusive=mutually_exclusive,
        sku_reject_patterns=tuple(str(item) for item in data.get("forbidden_patterns", ())),
        role_reject_patterns=role_patterns,
        formula=formula,
        description=str(data.get("description", "")),
        default_tier_by_stage={
            str(key): int(value)
            for key, value in dict(data.get("default_tier_by_stage", {})).items()
        },
        usage_mapping={str(key): str(value) for key, value in dict(data.get("usage_mapping", {})).items()},
        quantity_mapping={
            str(key): str(value) for key, value in dict(data.get("quantity_mapping", {})).items()
        },
        confidence_rules=dict(data.get("confidence_rules", {})),
        expected_monthly_ranges={
            str(scale): {
                "min": float(values.get("min", 0.0)),
                "max": float(values.get("max", 0.0)),
            }
            for scale, values in dict(expected_ranges).items()
            if isinstance(values, dict)
        },
    )


def _roles(values: Any) -> tuple[PricingRole, ...]:
    return tuple(PricingRole(str(value)) for value in values)


def _service_profile(service_name: str) -> ComponentProfile | None:
    lowered = service_name.casefold()
    if "cloud run" in lowered:
        return PROFILE_CLOUD_RUN
    if "lambda" in lowered:
        return PROFILE_LAMBDA
    if "fargate" in lowered or "ecs" in lowered:
        return PROFILE_ECS_FARGATE
    if "container apps" in lowered:
        return PROFILE_CONTAINER_APPS
    if "functions" in lowered:
        return PROFILE_AZURE_FUNCTIONS
    if "api management" in lowered or "apim" in lowered:
        return PROFILE_API_MANAGEMENT
    return None


def _database_profile(service_name: str) -> ComponentProfile:
    lowered = service_name.casefold()
    if any(token in lowered for token in ("dynamodb", "firestore", "cosmos")):
        return PROFILE_DATABASE_NOSQL
    return PROFILE_DATABASE_SQL


def resolve_component_profile(
    component_type: str,
    service_name: str,
    *,
    provider: str | None = None,
    repository: Any | None = None,
    allow_fallback: bool = True,
) -> ComponentProfile:
    resolution = resolve_component_profile_with_source(
        component_type,
        service_name,
        provider=provider,
        repository=repository,
        allow_fallback=allow_fallback,
    )
    if resolution.profile is None:
        raise LookupError("missing_pricing_profile")
    return resolution.profile


def resolve_component_profile_with_source(
    component_type: str,
    service_name: str,
    *,
    provider: str | None = None,
    repository: Any | None = None,
    allow_fallback: bool = False,
) -> ProfileResolution:
    normalized = COMPONENT_TYPE_ALIASES.get(component_type, component_type)
    if repository is not None and provider is not None:
        profile = repository.get_profile(
            provider=provider,
            component_type=normalized,
            cloud_service=service_name,
        )
        if profile is not None:
            return ProfileResolution(profile=profile, source="firestore")

    missing_data = ["missing_pricing_profile"]
    if not allow_fallback:
        return ProfileResolution(profile=None, missing_data=missing_data, source="missing")

    service = _service_profile(service_name)
    if service is not None and normalized in ("app_service", "queue_worker", "api_gateway"):
        return ProfileResolution(
            profile=service,
            missing_data=missing_data,
            source="fallback",
            used_fallback=True,
        )
    if normalized == "database":
        return ProfileResolution(
            profile=_database_profile(service_name),
            missing_data=missing_data,
            source="fallback",
            used_fallback=True,
        )
    fallback = BASE_PROFILE_BY_TYPE.get(normalized)
    if fallback is not None:
        return ProfileResolution(
            profile=fallback,
            missing_data=missing_data,
            source="fallback",
            used_fallback=True,
        )
    return ProfileResolution(
        profile=PROFILE_GENERIC,
        missing_data=missing_data,
        source="fallback",
        used_fallback=True,
    )
