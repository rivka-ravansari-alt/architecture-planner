"""Curated human engineering reviews for benchmark scenarios.

These reviews are written judgment — not generated from run output — and are
updated when pricing behavior materially changes.
"""

from __future__ import annotations

from pydantic import BaseModel


class HumanValidationReview(BaseModel):
    """Engineering review for one benchmark scenario."""

    scenario_id: str
    looks_realistic: bool
    realism_explanation: str
    largest_cost_drivers: tuple[str, ...]
    highest_impact_assumptions: tuple[str, ...]
    assumptions_to_refine: tuple[str, ...]
    service_selection_score: int
    review_summary: str


HUMAN_VALIDATION_REVIEWS: dict[str, HumanValidationReview] = {
    "simple_crud_saas": HumanValidationReview(
        scenario_id="simple_crud_saas",
        looks_realistic=True,
        realism_explanation=(
            "The ~$38/mo floor at 100 users matches Azure SQL Standard S1 (~$30) plus "
            "minimal Container Apps consumption. Growth to ~$8.4k at 100k users reflects "
            "linear API request scaling — reasonable for a CRUD API without caching assumptions."
        ),
        largest_cost_drivers=(
            "Azure SQL Database instance tier (flat S1 minimum)",
            "Azure Container Apps vCPU/memory seconds at scale",
            "Azure Blob Storage capacity + operations",
        ),
        highest_impact_assumptions=(
            "requests_per_month (sessions × requests per session)",
            "SQL tier selection (currently fixed Standard S1)",
            "storage_gb per user for exports and assets",
        ),
        assumptions_to_refine=(
            "SQL tier should escalate at 10k+ users rather than staying on S1",
            "Heuristic sessions/month may overstate B2B admin-panel usage vs consumer apps",
        ),
        service_selection_score=9,
        review_summary=(
            "Classic three-tier SaaS on Azure. Service choices are appropriate. The main "
            "gap is fixed SQL tier — real deployments would move to elastic pools or higher "
            "DTU/vCore tiers before 100k users."
        ),
    ),
    "self_esteem_habit": HumanValidationReview(
        scenario_id="self_esteem_habit",
        looks_realistic=True,
        realism_explanation=(
            "Costs track CRUD SaaS closely with a small Queue Storage increment for daily "
            "recommendation jobs. The reference benchmark scenario — totals are internally "
            "consistent and monotonic."
        ),
        largest_cost_drivers=(
            "Azure SQL Database S1 instance",
            "Azure Container Apps compute at scale",
            "Azure Queue Storage operations (background notifications)",
        ),
        highest_impact_assumptions=(
            "messages_per_user_per_month for queue operations",
            "Daily session frequency (drives API requests)",
            "Per-user SQL storage for progress history",
        ),
        assumptions_to_refine=(
            "Queue message rate for daily notifications vs batch digests",
            "Whether recommendation jobs run per-user daily or batched overnight",
        ),
        service_selection_score=9,
        review_summary=(
            "Queue Storage is the right lightweight choice for daily batch jobs vs Service Bus "
            "for this scale. Architecture matches a mobile habit-tracking MVP."
        ),
    ),
    "ecommerce": HumanValidationReview(
        scenario_id="ecommerce",
        looks_realistic=True,
        realism_explanation=(
            "Highest benchmark totals are expected: product images, order events, and webhook "
            "Functions add meaningful cost over CRUD. ~$25k/mo at 100k users is plausible for "
            "a mid-size storefront without CDN caching or reserved capacity discounts."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (product media at scale)",
            "Azure Service Bus operations (order/fulfillment events)",
            "Azure SQL Database + Container Apps",
        ),
        highest_impact_assumptions=(
            "storage_gb_per_user for product images",
            "messages_per_user_per_month on Service Bus",
            "Payment webhook invocation rate via Functions",
        ),
        assumptions_to_refine=(
            "Image optimization/CDN would reduce Blob egress in production",
            "Peak promotion traffic multipliers not modeled",
            "Functions execution duration for webhook handlers",
        ),
        service_selection_score=9,
        review_summary=(
            "Service Bus + Functions for order pipeline is standard Azure e-commerce patterns. "
            "Missing CDN/Front Door is acceptable for MVP costing but understates real-world "
            "optimizations."
        ),
    ),
    "ai_chat": HumanValidationReview(
        scenario_id="ai_chat",
        looks_realistic=True,
        realism_explanation=(
            "Azure infrastructure ~$10k/mo at 100k users is reasonable for API + Functions hosting. "
            "Critical caveat: external LLM API costs (OpenAI, etc.) are excluded and would "
            "typically dominate total spend — often 5–50× the Azure compute bill."
        ),
        largest_cost_drivers=(
            "Azure Container Apps (streaming chat API traffic)",
            "Azure Functions (LLM orchestration invocations)",
            "Azure Blob Storage (conversation archives)",
        ),
        highest_impact_assumptions=(
            "requests_per_session (multi-turn chat inflates API calls)",
            "ai=True traffic multiplier in heuristic builder",
            "Transcript storage_gb_per_user",
        ),
        assumptions_to_refine=(
            "Token usage and external LLM passthrough (not in Azure catalog)",
            "Streaming response duration affects Container Apps vCPU seconds",
            "Embedding storage and vector DB costs (not modeled)",
        ),
        service_selection_score=8,
        review_summary=(
            "Azure-side architecture is plausible for an LLM proxy pattern. Production AI chat "
            "budgets must add third-party model costs separately — this benchmark validates "
            "Azure hosting only."
        ),
    ),
    "ai_document_ocr": HumanValidationReview(
        scenario_id="ai_document_ocr",
        looks_realistic=True,
        realism_explanation=(
            "Low cost at 100 users (~$11) reflects async, bursty OCR without a database. "
            "Growth to ~$11k at 100k users is storage-dominated — consistent with retaining "
            "uploaded and processed documents."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (original + processed documents)",
            "Azure Functions (OCR worker invocations)",
            "Azure Queue Storage (job buffering)",
        ),
        highest_impact_assumptions=(
            "storage_gb_per_user for document uploads",
            "Queue/processing messages per uploaded document",
            "Functions execution time per page (not fully modeled)",
        ),
        assumptions_to_refine=(
            "Document retention policy (delete after processing vs archive)",
            "Azure AI Document Intelligence API costs (external service)",
            "Average pages per document",
        ),
        service_selection_score=9,
        review_summary=(
            "No SQL is correct for a stateless OCR pipeline with Blob as source of truth. "
            "Queue + Functions is the standard async processing pattern on Azure."
        ),
    ),
    "file_storage_drive": HumanValidationReview(
        scenario_id="file_storage_drive",
        looks_realistic=True,
        realism_explanation=(
            "~$23k/mo at 100k users with Blob as dominant cost matches a drive product where "
            "users accumulate gigabytes. SQL metadata cost stays near the S1 floor — "
            "appropriate for folder indexing only."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (user file content — 60%+ of total at scale)",
            "Azure SQL Database instance",
            "Azure Container Apps (metadata/sync API)",
        ),
        highest_impact_assumptions=(
            "storage_gb_per_user (primary cost lever)",
            "reads_per_user_per_month (sync and preview traffic)",
            "writes_per_user_per_month (upload frequency)",
        ),
        assumptions_to_refine=(
            "Per-user storage cap and deduplication",
            "Cold/archive tier for inactive files",
            "Client-side sync reducing read operations",
        ),
        service_selection_score=9,
        review_summary=(
            "Architecture correctly separates metadata (SQL) from content (Blob). Real drive "
            "products often add Azure Files or multi-region replication — not in current catalog."
        ),
    ),
    "social_network": HumanValidationReview(
        scenario_id="social_network",
        looks_realistic=True,
        realism_explanation=(
            "Similar cost profile to file storage drive plus Service Bus for notifications. "
            "~$23k/mo at 100k users is plausible for an MVP social app without feed caching, "
            "CDN, or Cosmos DB for the social graph."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (photos and media)",
            "Azure SQL Database (social graph — may underestimate at scale)",
            "Azure Service Bus (notification fan-out)",
        ),
        highest_impact_assumptions=(
            "storage_gb_per_user for media uploads",
            "messages_per_user_per_month on Service Bus",
            "Feed read frequency (API requests)",
        ),
        assumptions_to_refine=(
            "SQL Database is unlikely to hold 100k-user social graphs efficiently — Cosmos DB "
            "would be more realistic at scale",
            "Feed fan-out read amplification not fully modeled",
            "Media CDN caching would reduce egress",
        ),
        service_selection_score=7,
        review_summary=(
            "MVP mapping uses SQL for simplicity; at 100k users a NoSQL graph store would be "
            "more realistic. Benchmark still validates messaging + media cost scaling."
        ),
    ),
    "video_processing": HumanValidationReview(
        scenario_id="video_processing",
        looks_realistic=True,
        realism_explanation=(
            "Async pipeline without SQL mirrors OCR. Storage growth dominates. Actual transcode "
            "compute (ffmpeg GPU time) is stubbed via Functions invocations — real video "
            "platforms would show higher compute costs."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (raw + transcoded video)",
            "Azure Functions (transcode workers — duration understated)",
            "Azure Queue Storage (job scheduling)",
        ),
        highest_impact_assumptions=(
            "storage_gb_per_user for video files",
            "Processing jobs per upload",
            "Functions memory/duration for transcoding (needs product-specific tuning)",
        ),
        assumptions_to_refine=(
            "Average video size and bitrate (GB per minute)",
            "GPU/accelerated compute tier for transcoding",
            "Output renditions count (720p + 1080p doubles storage)",
        ),
        service_selection_score=8,
        review_summary=(
            "Queue + Functions + Blob is the correct Azure async video pattern. Compute cost "
            "for transcoding is the weakest estimate — Functions defaults understate ffmpeg runs."
        ),
    ),
    "background_job_platform": HumanValidationReview(
        scenario_id="background_job_platform",
        looks_realistic=True,
        realism_explanation=(
            "No SQL floor keeps 100-user cost low (~$17). Dual messaging (Service Bus + Queue) "
            "plus Functions reflects a job orchestration platform. ~$6.7k at 100k users is "
            "reasonable for message-heavy workloads."
        ),
        largest_cost_drivers=(
            "Azure Functions (job handler invocations)",
            "Azure Service Bus + Queue Storage operations",
            "Azure Container Apps (job submission API)",
        ),
        highest_impact_assumptions=(
            "messages_per_user_per_month across both queues",
            "Functions invocations per job",
            "Job payload size (affects messaging storage/egress)",
        ),
        assumptions_to_refine=(
            "Long-running jobs may need Container Apps workers instead of Functions",
            "Duplicate messaging paths (Service Bus + Queue) may overcount",
            "Retry policy multiplying message operations",
        ),
        service_selection_score=8,
        review_summary=(
            "Dual-queue architecture validates messaging cost paths. Production job platforms "
            "often consolidate on Service Bus or Event Hubs — benchmark intentionally exercises both."
        ),
    ),
    "analytics_dashboard": HumanValidationReview(
        scenario_id="analytics_dashboard",
        looks_realistic=True,
        realism_explanation=(
            "Nearly identical to Simple CRUD SaaS — expected for read-heavy SQL + API + "
            "periodic report exports. Scheduled PDF generation adds only modest Blob cost."
        ),
        largest_cost_drivers=(
            "Azure SQL Database S1 instance",
            "Azure Container Apps API traffic",
            "Azure Blob Storage (report exports)",
        ),
        highest_impact_assumptions=(
            "Read-heavy API request rate",
            "SQL storage for aggregated metrics",
            "Report export frequency and file size",
        ),
        assumptions_to_refine=(
            "SQL analytics at scale often uses Synapse or dedicated warehouse tiers",
            "Pre-aggregated rollups reduce query load vs modeled per-request reads",
        ),
        service_selection_score=8,
        review_summary=(
            "SQL + Blob exports is valid for SMB analytics. Enterprise BI would add Synapse, "
            "Fabric, or Power BI licensing outside this catalog."
        ),
    ),
    "static_website": HumanValidationReview(
        scenario_id="static_website",
        looks_realistic=True,
        realism_explanation=(
            "No SQL removes the ~$30/mo floor — ~$4/mo at 100 users vs ~$38 for CRUD SaaS. "
            "This confirms the engine can price non-database architectures. At 100k users, "
            "Blob read/egress scaling dominates (~$4k) — a static site with high traffic would "
            "normally use Azure CDN/Front Door (not yet in catalog)."
        ),
        largest_cost_drivers=(
            "Azure Blob Storage (static assets + egress at scale)",
            "Azure Functions (contact form submissions only)",
        ),
        highest_impact_assumptions=(
            "Page views modeled as Blob read operations",
            "Static asset size per page load",
            "Contact form submissions per user (Functions invocations)",
        ),
        assumptions_to_refine=(
            "Azure Static Web Apps or CDN would replace direct Blob egress",
            "Marketing sites have spiky campaign traffic not captured in MAU bands",
            "Cache hit ratio dramatically reduces origin reads",
        ),
        service_selection_score=7,
        review_summary=(
            "Blob + Functions is a reasonable MVP stand-in for static hosting. Missing Static "
            "Web Apps / Front Door means high-traffic estimates overstate origin Blob costs — "
            "but the low-user baseline correctly differs from CRUD SaaS."
        ),
    ),
}


def get_human_validation(scenario_id: str) -> HumanValidationReview | None:
    return HUMAN_VALIDATION_REVIEWS.get(scenario_id)
