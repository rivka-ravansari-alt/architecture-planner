"""Benchmark scenario definitions for Azure pricing validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.domain import MappedComponent


@dataclass(frozen=True)
class ArchitectureComponentSpec:
    """One component in a benchmark architecture."""

    key: str
    name: str
    component_type: str
    reason: str
    azure_service: str
    aws_service: str = "Lambda"
    gcp_service: str = "Cloud Run"
    category: str = "core"
    optional: bool = False
    order: int = 0


@dataclass(frozen=True)
class BenchmarkScenario:
    """Full benchmark scenario for Azure pricing validation."""

    scenario_id: str
    name: str
    product_description: str
    expected_architecture: str
    service_rationale: str
    stage: str = "mvp"
    feature_flags: dict[str, bool] = field(default_factory=dict)
    components: tuple[ArchitectureComponentSpec, ...] = ()


def _comp(
    key: str,
    name: str,
    component_type: str,
    reason: str,
    azure_service: str,
    *,
    order: int,
    aws_service: str = "Lambda",
    gcp_service: str = "Cloud Run",
) -> ArchitectureComponentSpec:
    return ArchitectureComponentSpec(
        key=key,
        name=name,
        component_type=component_type,
        reason=reason,
        azure_service=azure_service,
        aws_service=aws_service,
        gcp_service=gcp_service,
        order=order,
    )


def _mapped_components(specs: tuple[ArchitectureComponentSpec, ...]) -> list[MappedComponent]:
    return [
        MappedComponent(
            key=spec.key,
            name=spec.name,
            component_type=spec.component_type,
            reason=spec.reason,
            category=spec.category,
            optional=spec.optional,
            order=spec.order,
            cloud={
                "aws": spec.aws_service,
                "gcp": spec.gcp_service,
                "azure": spec.azure_service,
            },
        )
        for spec in specs
    ]


def _scenario(
    scenario_id: str,
    name: str,
    product_description: str,
    expected_architecture: str,
    service_rationale: str,
    *,
    components: tuple[ArchitectureComponentSpec, ...],
    feature_flags: dict[str, bool] | None = None,
    stage: str = "mvp",
) -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id=scenario_id,
        name=name,
        product_description=product_description,
        expected_architecture=expected_architecture,
        service_rationale=service_rationale,
        stage=stage,
        feature_flags=feature_flags or {},
        components=components,
    )


SIMPLE_CRUD_SAAS = _scenario(
    "simple_crud_saas",
    "Simple CRUD SaaS",
    (
        "A lightweight B2B SaaS product for managing records (customers, tasks, or "
        "inventory). Users sign in, create and edit records, search lists, and export "
        "CSV reports. Traffic is steady with moderate read/write ratios and minimal "
        "background processing."
    ),
    "Azure Container Apps (API) + Azure SQL Database + Azure Blob Storage (exports/assets)",
    (
        "Container Apps provides autoscaling HTTP APIs without managing VMs. SQL Database "
        "handles relational CRUD with predictable DTU tiers. Blob Storage stores export "
        "files and static assets at low cost."
    ),
    feature_flags={"file_upload": False, "ai": False, "background_processing": False},
    components=(
        _comp(
            "api",
            "Backend API",
            "service",
            "REST API for CRUD operations and authentication",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Primary Database",
            "database",
            "Relational storage for users, records, and metadata",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Object Storage",
            "object_storage",
            "CSV exports, logos, and lightweight attachments",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
    ),
)

SELF_ESTEEM_HABIT = _scenario(
    "self_esteem_habit",
    "Self-Esteem / Habit Tracking",
    (
        "A self-esteem improvement application that provides users with daily exercises "
        "designed to build confidence, positive self-image, and emotional well-being. "
        "Users complete exercises, track progress, maintain daily streaks, and receive "
        "personalized recommendations. The system stores user progress and provides a "
        "simple dashboard to visualize growth over time."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage + Azure Queue Storage",
    (
        "Container Apps hosts the mobile/web API. SQL Database stores exercises, streaks, "
        "and progress history. Blob Storage holds dashboard assets. Queue Storage runs "
        "daily recommendation and notification background jobs."
    ),
    feature_flags={"file_upload": False, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Backend/API",
            "service",
            "REST API for exercises, progress, streaks, and dashboard",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Database",
            "database",
            "User progress, exercises, streaks, and recommendations",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Object Storage",
            "object_storage",
            "Static assets and lightweight user content for dashboard",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
        _comp(
            "notifications",
            "Daily Recommendations Queue",
            "queue",
            "Background jobs for daily recommendations and notifications",
            "Queue Storage",
            aws_service="SQS",
            gcp_service="Cloud Tasks",
            order=3,
        ),
    ),
)

ECOMMERCE = _scenario(
    "ecommerce",
    "E-Commerce Application",
    (
        "An online store where customers browse catalogs, manage carts, place orders, "
        "and receive order confirmations. Merchants manage inventory and fulfill orders. "
        "The platform handles payment webhooks, order state transitions, and periodic "
        "inventory sync jobs with moderate peak traffic during promotions."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage + Azure Service Bus + Azure Functions",
    (
        "Container Apps serves storefront and admin APIs. SQL Database stores catalog, "
        "orders, and inventory. Blob Storage hosts product images. Service Bus decouples "
        "order fulfillment and inventory events. Functions handle payment webhooks and "
        "scheduled sync tasks."
    ),
    feature_flags={"file_upload": True, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Storefront API",
            "service",
            "Product catalog, cart, checkout, and order APIs",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Order Database",
            "database",
            "Products, orders, customers, and inventory",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Product Media Storage",
            "object_storage",
            "Product images, thumbnails, and downloadable receipts",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
        _comp(
            "queue",
            "Order Events",
            "queue",
            "Order placement, fulfillment, and inventory events",
            "Service Bus",
            aws_service="SQS",
            gcp_service="Pub/Sub",
            order=3,
        ),
        _comp(
            "webhooks",
            "Payment Webhooks",
            "worker",
            "Payment provider webhooks and scheduled inventory sync",
            "Azure Functions",
            order=4,
        ),
    ),
)

AI_CHAT = _scenario(
    "ai_chat",
    "AI Chat Application",
    (
        "A conversational AI assistant where users send prompts, receive streamed "
        "responses, and maintain conversation history. Each session involves multiple "
        "round-trips to an external LLM API with token usage tracked per user. "
        "Conversation transcripts and embeddings are persisted for context retrieval."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage + Azure Functions",
    (
        "Container Apps hosts the chat API with streaming responses. SQL Database stores "
        "conversation metadata and user accounts. Blob Storage archives long transcripts "
        "and embedding caches. Functions orchestrate LLM calls, token accounting, and "
        "async summarization jobs."
    ),
    feature_flags={"file_upload": False, "ai": True, "background_processing": True},
    components=(
        _comp(
            "api",
            "Chat API",
            "service",
            "Streaming chat endpoints and session management",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Conversation Database",
            "database",
            "Users, sessions, message metadata, and usage counters",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Transcript Storage",
            "object_storage",
            "Long conversation archives and embedding caches",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
        _comp(
            "llm_worker",
            "LLM Orchestration",
            "worker",
            "LLM proxy calls, summarization, and token metering",
            "Azure Functions",
            order=3,
        ),
    ),
)

AI_DOCUMENT_OCR = _scenario(
    "ai_document_ocr",
    "AI Document Processing / OCR",
    (
        "A document intelligence platform where users upload PDFs and images for OCR, "
        "text extraction, and structured data extraction. Documents are processed "
        "asynchronously with progress tracking. Processed outputs include searchable "
        "text, extracted fields, and confidence scores."
    ),
    "Azure Container Apps + Azure Blob Storage + Azure Queue Storage + Azure Functions",
    (
        "Container Apps provides upload status and results APIs. Blob Storage holds "
        "original documents and processed outputs at scale. Queue Storage buffers "
        "processing jobs. Functions run OCR and extraction pipelines triggered by queue "
        "messages."
    ),
    feature_flags={"file_upload": True, "ai": True, "background_processing": True},
    components=(
        _comp(
            "api",
            "Document API",
            "service",
            "Upload, status polling, and results retrieval",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "files",
            "Document Storage",
            "object_storage",
            "Original uploads and processed document outputs",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=1,
        ),
        _comp(
            "queue",
            "Processing Queue",
            "queue",
            "Async OCR and extraction job queue",
            "Queue Storage",
            aws_service="SQS",
            gcp_service="Cloud Tasks",
            order=2,
        ),
        _comp(
            "processor",
            "OCR Worker",
            "worker",
            "Document OCR, extraction, and AI enrichment",
            "Azure Functions",
            order=3,
        ),
    ),
)

FILE_STORAGE_DRIVE = _scenario(
    "file_storage_drive",
    "File Storage / Drive Application",
    (
        "A cloud drive application where users upload, sync, share, and download files "
        "across devices. Storage grows linearly with users. Read traffic dominates "
        "writes due to frequent file access and preview generation. Minimal compute "
        "beyond metadata APIs."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage",
    (
        "Container Apps serves file metadata and sharing APIs. SQL Database indexes "
        "folders, permissions, and sync state. Blob Storage is the primary cost driver "
        "for user file content at scale."
    ),
    feature_flags={"file_upload": True, "ai": False, "background_processing": False},
    components=(
        _comp(
            "api",
            "Drive API",
            "service",
            "File metadata, sharing links, and sync coordination",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Metadata Database",
            "database",
            "Folder structure, permissions, and sync tokens",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "User File Storage",
            "object_storage",
            "Primary user file content and version snapshots",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
    ),
)

SOCIAL_NETWORK = _scenario(
    "social_network",
    "Social Network",
    (
        "A social platform where users create profiles, post updates, follow others, "
        "like and comment on content, and receive activity notifications. Feed reads "
        "dominate write volume. Real-time notifications and activity fan-out require "
        "async messaging at scale."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage + Azure Service Bus",
    (
        "Container Apps hosts feed and profile APIs. SQL Database stores users, posts, "
        "and relationships. Blob Storage holds media attachments and avatars. Service "
        "Bus handles notification fan-out and activity events."
    ),
    feature_flags={"file_upload": True, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Social API",
            "service",
            "Profiles, feeds, posts, likes, and comments",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Social Graph Database",
            "database",
            "Users, posts, follows, and engagement data",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Media Storage",
            "object_storage",
            "Photos, videos, and avatar images",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
        _comp(
            "events",
            "Activity Events",
            "queue",
            "Notification fan-out and activity stream events",
            "Service Bus",
            aws_service="SQS",
            gcp_service="Pub/Sub",
            order=3,
        ),
    ),
)

VIDEO_PROCESSING = _scenario(
    "video_processing",
    "Video Processing Application",
    (
        "A platform where users upload videos for transcoding, thumbnail generation, "
        "and streaming delivery. Uploads are large; processing is CPU-intensive and "
        "fully asynchronous. Processed outputs are served via CDN-like download patterns."
    ),
    "Azure Container Apps + Azure Blob Storage + Azure Queue Storage + Azure Functions",
    (
        "Container Apps handles upload coordination and playback metadata. Blob Storage "
        "stores raw and transcoded video at high volume. Queue Storage schedules "
        "transcoding jobs. Functions run ffmpeg-style processing pipelines."
    ),
    feature_flags={"file_upload": True, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Video API",
            "service",
            "Upload coordination, job status, and playback metadata",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "files",
            "Video Storage",
            "object_storage",
            "Raw uploads and transcoded output files",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=1,
        ),
        _comp(
            "queue",
            "Transcode Queue",
            "queue",
            "Video transcoding and thumbnail job queue",
            "Queue Storage",
            aws_service="SQS",
            gcp_service="Cloud Tasks",
            order=2,
        ),
        _comp(
            "worker",
            "Transcode Worker",
            "worker",
            "Video transcoding and thumbnail generation",
            "Azure Functions",
            order=3,
        ),
    ),
)

BACKGROUND_JOB_PLATFORM = _scenario(
    "background_job_platform",
    "Background Job Processing Platform",
    (
        "A job orchestration platform where developers enqueue tasks (email sends, "
        "report generation, data imports) via API. Workers pull jobs from queues, "
        "process them with retries, and report completion. High message throughput "
        "with variable job durations."
    ),
    "Azure Container Apps + Azure Service Bus + Azure Queue Storage + Azure Functions",
    (
        "Container Apps provides job submission and status APIs. Service Bus handles "
        "priority and fan-out messaging. Queue Storage buffers bulk job batches. "
        "Functions execute short-lived job handlers at scale."
    ),
    feature_flags={"file_upload": False, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Job API",
            "service",
            "Job submission, status polling, and scheduling",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "service_bus",
            "Priority Messaging",
            "queue",
            "Priority job routing and worker fan-out",
            "Service Bus",
            aws_service="SQS",
            gcp_service="Pub/Sub",
            order=1,
        ),
        _comp(
            "queue",
            "Bulk Job Queue",
            "queue",
            "Bulk batch job buffering",
            "Queue Storage",
            aws_service="SQS",
            gcp_service="Cloud Tasks",
            order=2,
        ),
        _comp(
            "worker",
            "Job Workers",
            "worker",
            "Short-lived job handlers and retry logic",
            "Azure Functions",
            order=3,
        ),
    ),
)

ANALYTICS_DASHBOARD = _scenario(
    "analytics_dashboard",
    "Analytics / Reporting Dashboard",
    (
        "A business intelligence dashboard where users connect data sources, run "
        "aggregated queries, and view charts and scheduled reports. Read-heavy workload "
        "with periodic batch report generation. Data is pre-aggregated in SQL with "
        "exported reports stored as files."
    ),
    "Azure Container Apps + Azure SQL Database + Azure Blob Storage",
    (
        "Container Apps serves dashboard APIs and report endpoints. SQL Database "
        "stores aggregated metrics and user configurations with read-heavy query "
        "patterns. Blob Storage archives scheduled report exports."
    ),
    feature_flags={"file_upload": False, "ai": False, "background_processing": True},
    components=(
        _comp(
            "api",
            "Dashboard API",
            "service",
            "Chart data, filters, and report download endpoints",
            "Azure Container Apps",
            order=0,
        ),
        _comp(
            "database",
            "Analytics Database",
            "database",
            "Aggregated metrics, dashboards, and query definitions",
            "SQL Database",
            aws_service="RDS PostgreSQL",
            gcp_service="Cloud SQL",
            order=1,
        ),
        _comp(
            "files",
            "Report Exports",
            "object_storage",
            "Scheduled PDF/CSV report exports",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=2,
        ),
    ),
)

STATIC_WEBSITE = _scenario(
    "static_website",
    "Static Website / Marketing Landing Page",
    (
        "A marketing landing page with static HTML, CSS, JavaScript, images, and a "
        "simple contact form. Traffic is mostly anonymous page views with occasional "
        "form submissions. No user accounts, no database, and minimal server-side logic."
    ),
    "Azure Blob Storage (static assets) + Azure Functions (contact form handler)",
    (
        "Blob Storage hosts static site files — the CDN/static-hosting pattern on Azure. "
        "Functions handles occasional form POSTs at near-zero scale. No SQL Database "
        "deliberately, to verify the engine does not assume every app is CRUD SaaS."
    ),
    feature_flags={"file_upload": False, "ai": False, "background_processing": False},
    components=(
        _comp(
            "static",
            "Static Site Assets",
            "object_storage",
            "HTML, CSS, JS, images, and downloadable assets",
            "Blob Storage",
            aws_service="S3",
            gcp_service="Cloud Storage",
            order=0,
        ),
        _comp(
            "forms",
            "Contact Form Handler",
            "worker",
            "Serverless handler for contact form submissions",
            "Azure Functions",
            order=1,
        ),
    ),
)

ALL_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    SIMPLE_CRUD_SAAS,
    SELF_ESTEEM_HABIT,
    ECOMMERCE,
    AI_CHAT,
    AI_DOCUMENT_OCR,
    FILE_STORAGE_DRIVE,
    SOCIAL_NETWORK,
    VIDEO_PROCESSING,
    BACKGROUND_JOB_PLATFORM,
    ANALYTICS_DASHBOARD,
    STATIC_WEBSITE,
)

SCENARIOS_BY_ID: dict[str, BenchmarkScenario] = {
    scenario.scenario_id: scenario for scenario in ALL_BENCHMARK_SCENARIOS
}


def scenario_components(scenario: BenchmarkScenario) -> list[MappedComponent]:
    """Return MappedComponent list for a benchmark scenario."""
    return _mapped_components(scenario.components)


def self_esteem_scenario_definition() -> BenchmarkScenario:
    """Backward-compatible alias for the original self-esteem benchmark."""
    return SELF_ESTEEM_HABIT
