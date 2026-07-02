"""Classify Firestore catalog SKUs into semantic pricing roles (profile-gated)."""

from __future__ import annotations

from typing import Any

from app.services.pricing.component_profiles import ComponentProfile, PricingRole

GLOBAL_SKIP = (
    "ssh",
    "transfer_protocol",
    "batchoperations",
    "restoreobject",
    "manifest",
    "waf",
    "portal_product",
    "premiuminternet",
)

NETWORK_EXCLUDE = (
    "egress",
    "ingress",
    "transfer",
    "peering",
    "interconnect",
    "interregion",
    "inter-region",
    "network internet",
    "cdn",
    "draops",
)

STORAGE_EXCLUDE = NETWORK_EXCLUDE + (
    "restore",
    "backup",
    "export",
    "import",
    "pool",
    "pooling",
    "long-term",
)

HOSTING_EXCLUDE = STORAGE_EXCLUDE + (
    "front door",
    "frontdoor",
    "cdn",
    "firewall",
    "add-on",
    "addon",
)

AI_EXCLUDE = (
    "commit",
    "commitment",
    "reserved",
    "batch",
    "tuning",
    "training",
    "provisioned",
    "ft_",
    "_ft",
    "fine",
    "hosting",
    "trng",
    "hstng",
)

AI_MODALITY_EXCLUDE = (
    "speech",
    "text_to_speech",
    "text-to-speech",
    "tts",
    "whisper",
    "dall",
    "audio",
    "video",
    "moderation",
    "realtime",
)


def _haystack(role: str, sku: dict[str, Any]) -> str:
    return " ".join(
        [
            role,
            str(sku.get("description", "")),
            str(sku.get("usage_unit", "")),
            str(sku.get("product_family", "")),
        ]
    ).lower()


def _contains(haystack: str, tokens: tuple[str, ...]) -> bool:
    return any(token in haystack for token in tokens)


def _contains_storage_exclude(haystack: str) -> bool:
    tokens = STORAGE_EXCLUDE
    if "firestore" in haystack:
        tokens = tuple(token for token in STORAGE_EXCLUDE if token != "restore")
    return _contains(haystack, tokens)


def _contains_profile_reject(haystack: str, tokens: tuple[str, ...]) -> bool:
    if "firestore" in haystack:
        tokens = tuple(token for token in tokens if token != "restore")
    return _contains(haystack, tokens)


def classify_sku(catalog_role: str, sku: dict[str, Any]) -> PricingRole | None:
    """Classify a catalog SKU into a semantic pricing role (no profile filter)."""
    haystack = _haystack(catalog_role, sku)
    unit = str(sku.get("usage_unit", "")).lower()

    if _contains(haystack, GLOBAL_SKIP):
        return None

    scores: list[tuple[float, PricingRole]] = []

    def add(score: float, role: PricingRole) -> None:
        if score < 500:
            scores.append((score, role))

    if _contains(haystack, ("egress", "data transfer", "outbound")) and "restore" not in haystack:
        add(1 if "egress" in haystack else 5, PricingRole.EGRESS)
        add(2, PricingRole.DATA_TRANSFER)

    if _contains(haystack, ("gateway unit", "api management", "apim", "loadbalancer-hour", "load balancer-hour")) or (
        "gateway" in haystack and ("hour" in unit or "1 hour" in haystack)
    ):
        if not _contains(haystack, NETWORK_EXCLUDE):
            add(1, PricingRole.GATEWAY_CAPACITY)

    if ("cache" in haystack or "redis" in haystack) and (
        "node" in haystack or "instance" in haystack or "elasticache" in haystack
    ):
        add(2, PricingRole.CACHE_INSTANCE)

    if _looks_like_instance(haystack) and not _contains_storage_exclude(haystack):
        add(3, PricingRole.INSTANCE)

    if ("cpu" in haystack or "vcpu" in haystack) and "memory" not in haystack:
        if not _contains(haystack, NETWORK_EXCLUDE + ("front door", "streaming")):
            add(1, PricingRole.CPU)

    if ("memory" in haystack or " ram" in haystack) and not _contains(haystack, NETWORK_EXCLUDE):
        if "gb-second" not in haystack and "streaming" not in haystack:
            add(1, PricingRole.MEMORY)

    if (
        catalog_role == "requests"
        or unit in {"request", "requests", "count"}
        and _contains(haystack, ("request", "requests"))
    ):
        add(0.5, PricingRole.REQUESTS)

    if "gb-second" in haystack or "gb second" in haystack or "gb-seconds" in haystack:
        if "streaming" not in haystack:
            add(1, PricingRole.GB_SECONDS)

    if _contains(haystack, ("execution", "executions", "invoke")) and not _contains(haystack, NETWORK_EXCLUDE):
        add(2, PricingRole.EXECUTION)

    if "mau" in haystack or "monthly active" in haystack:
        add(1, PricingRole.MAU)

    if _contains(haystack, ("sms", "mfa", "phone verification")):
        add(1, PricingRole.SMS_MFA)
    if _contains(haystack, ("signin", "sign-in", "auth event", "login")):
        add(3, PricingRole.AUTH_EVENTS)

    if not _contains(haystack, AI_EXCLUDE + AI_MODALITY_EXCLUDE):
        if _contains(haystack, ("gemini", "prediction", "bedrock", "anthropic", "llama")):
            if "hour" not in unit:
                add(1, PricingRole.INFERENCE)
        elif "embedding" in haystack:
            add(2, PricingRole.INFERENCE)
        elif "output" in haystack and "token" in haystack:
            add(1, PricingRole.OUTPUT_TOKENS)
        elif "input" in haystack and "token" in haystack:
            add(1, PricingRole.INPUT_TOKENS)
        elif catalog_role == "tokens" or ("token" in haystack and "hour" not in unit):
            add(2, PricingRole.INFERENCE)

    if _contains(haystack, ("message delivery", "publish", "subscription", "queue message", "service bus", "pub/sub")):
        queue_excludes = NETWORK_EXCLUDE + ("cloud storage", "tiby", "gcs")
        if "message delivery basic" in haystack:
            queue_excludes = NETWORK_EXCLUDE + ("cloud storage", "gcs")
        if not _contains(haystack, queue_excludes):
            if "firebase subscription" not in haystack:
                add(2, PricingRole.QUEUE_MESSAGES)

    if _contains(haystack, ("ingest", "log", "metric")) and "restore" not in haystack:
        add(2, PricingRole.LOG_INGESTION)

    if _contains(haystack, ("class a", "put", "write op", "writes", "delete ops", "deletes")) and not _contains_storage_exclude(haystack):
        add(2, PricingRole.WRITE_OPERATIONS)
    if _contains(haystack, ("class b", "get", "read op", "read ops")) and not _contains_storage_exclude(haystack):
        add(2, PricingRole.READ_OPERATIONS)

    if _contains(haystack, ("read", "write", "document")) and "restore" not in haystack:
        if "backup" not in haystack:
            add(4, PricingRole.READ_OPERATIONS)
            add(4, PricingRole.WRITE_OPERATIONS)

    storage_tokens = ("storage", "stored", "gib", "gb-month", "gb/month", "blob", "lrs", "data capacity")
    if _contains(haystack, storage_tokens):
        firestore_storage = "firestore" in haystack and "backup storage" in haystack
        cosmos_storage = "data capacity" in haystack or ("cosmos" in haystack and "stored" in haystack)
        if firestore_storage or cosmos_storage or not _contains_storage_exclude(haystack):
            add(90 if _contains(haystack, ("instance", "nodeusage", "vcpu")) else 1, PricingRole.STORAGE)

    if _contains(haystack, ("backup", "snapshot")) and "restore" not in haystack:
        add(5, PricingRole.BACKUP)

    if not _contains(haystack, HOSTING_EXCLUDE):
        if _contains(haystack, ("hosting", "amplify", "static", "firebase hosting", "app service plan", "firebase subscription")):
            add(2, PricingRole.HOSTING)
            if "compute" in haystack or "gb-hour" in haystack:
                add(3, PricingRole.COMPUTE)

    if not _contains(haystack, NETWORK_EXCLUDE + HOSTING_EXCLUDE):
        if _contains(haystack, ("api call", "call", "calls", "invocation", "request", "operation")):
            if "connection minute" not in haystack:
                add(3, PricingRole.REQUESTS)
        if haystack.endswith("requests") or " per request" in haystack:
            add(4, PricingRole.REQUESTS)

    if not scores:
        return None
    scores.sort(key=lambda item: item[0])
    return scores[0][1]


def evaluate_sku_for_role(
    catalog_role: str,
    sku: dict[str, Any],
    profile: ComponentProfile,
    target_role: PricingRole,
) -> tuple[bool, str | None]:
    """Return whether a catalog SKU may be used for target_role under profile rules."""
    if not profile.allows(target_role):
        return False, f"role {target_role.value} not allowed by profile"

    classified = classify_sku(catalog_role, sku)
    if classified is None:
        return False, "unclassified SKU"
    if classified != target_role:
        return False, f"classified as {classified.value}, not {target_role.value}"
    if profile.is_forbidden(classified):
        return False, f"forbidden role {classified.value}"

    haystack = _haystack(catalog_role, sku)
    if _contains_profile_reject(haystack, profile.reject_patterns_for(target_role)):
        return False, "forbidden SKU pattern for profile"

    return True, None


def iter_skus_for_role(
    skus: dict[str, dict[str, Any]],
    profile: ComponentProfile,
    pricing_role: PricingRole,
    *,
    reject_log: list[dict[str, str]] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Return catalog SKUs matching target_role that pass profile gates."""
    if not profile.allows(pricing_role):
        return []

    matched: list[tuple[str, dict[str, Any]]] = []
    for catalog_role, sku in skus.items():
        ok, reason = evaluate_sku_for_role(catalog_role, sku, profile, pricing_role)
        if ok:
            matched.append((catalog_role, sku))
        elif reject_log is not None and reason:
            reject_log.append(
                {
                    "catalog_role": catalog_role,
                    "sku_id": str(sku.get("sku_id", catalog_role)),
                    "target_role": pricing_role.value,
                    "reason": reason,
                }
            )
    return matched


def _looks_like_instance(haystack: str) -> bool:
    if _contains(haystack, ("storage", "backup", "snapshot", "iops")):
        if "instance" not in haystack and "nodeusage" not in haystack:
            return False
    return _contains(
        haystack,
        ("instanceusage", "instance", "nodeusage", "db.", "dedicated", "vcpu", "sql", "dtu", "vcore"),
    )
