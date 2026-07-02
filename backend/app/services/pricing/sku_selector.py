"""Select a small relevant SKU subset from large Firestore catalog documents."""

from __future__ import annotations

from typing import Any

SKU_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "requests": ("request", "call", "operation", "ops", "api"),
    "storage": ("storage", "stored", "byte", "gib", "gb", "lrs", "grs", "zrs", "blob"),
    "egress": ("egress", "transfer", "network", "cdn", "outbound"),
    "compute": ("cpu", "vcpu", "core", "duration", "memory", "ram", "execution", "lambda"),
    "hosting": ("host", "app", "instance", "unit", "plan", "standard", "basic"),
}

COMPONENT_SKU_CATEGORIES: dict[str, tuple[str, ...]] = {
    "object_storage": ("storage", "requests", "egress"),
    "api_gateway": ("requests", "compute", "egress"),
    "api": ("requests", "compute", "egress"),
    "app_service": ("compute", "requests"),
    "service": ("compute", "requests"),
    "web_app": ("hosting", "requests", "storage", "egress"),
    "mobile_app": ("hosting", "requests", "storage"),
    "admin_panel": ("hosting", "requests", "storage"),
    "auth": ("requests", "hosting"),
    "authentication": ("requests", "hosting"),
    "database": ("storage", "compute", "requests"),
    "cdn": ("egress", "requests"),
    "queue_worker": ("compute", "requests"),
    "queue": ("compute", "requests"),
    "worker": ("compute", "requests"),
    "ai_service": ("requests", "compute"),
    "ai_provider": ("requests", "compute"),
    "cache": ("storage", "compute"),
    "search": ("storage", "compute", "requests"),
}

DEFAULT_SKU_CATEGORIES: tuple[str, ...] = ("requests", "storage", "compute")
SERVICE_FORMULA_MARKERS: frozenset[str] = frozenset(
    {
        "cpu_cost",
        "memory_cost",
        "request_cost",
        "duration_cost",
        "execution_cost",
        "vcpu_cost",
    }
)


SKIP_ROLE_KEYWORDS: tuple[str, ...] = (
    "ssh",
    "transfer_protocol",
    "batchoperations",
    "restoreobject",
    "manifest",
    "premiuminternet",
    "portal_product",
    "waf",
)


def filter_skus_for_estimate(
    skus: dict[str, dict[str, Any]],
    component_type: str,
    *,
    formula: dict[str, str] | None = None,
    max_skus: int = 4,
) -> tuple[dict[str, dict[str, Any]], bool]:
    if formula and _is_service_specific_formula(formula):
        referenced = _roles_referenced_in_formula(formula)
        selected = {
            role: skus[role]
            for role in referenced
            if role in skus and not _should_skip_role(role, skus[role])
        }
        if selected:
            return selected, len(selected) < len(skus)

    if len(skus) <= max_skus:
        return skus, False

    categories = COMPONENT_SKU_CATEGORIES.get(component_type, DEFAULT_SKU_CATEGORIES)
    selected: dict[str, dict[str, Any]] = {}
    for category in categories:
        role = _best_role_for_category(skus, SKU_CATEGORY_KEYWORDS.get(category, (category,)))
        if role and role not in selected:
            selected[role] = skus[role]
        if len(selected) >= max_skus:
            break

    if not selected:
        ranked = sorted(
            skus.items(),
            key=lambda item: float(item[1].get("unit_price_usd", 0.0)),
        )
        selected = dict(ranked[:max_skus])

    return selected, True


def rebuild_formula(
    skus: dict[str, dict[str, Any]],
    original_formula: dict[str, str],
) -> dict[str, str]:
    if _is_service_specific_formula(original_formula):
        return dict(original_formula)

    if not skus:
        return {"total": "0"}

    formula: dict[str, str] = {}
    cost_terms: list[str] = []
    for role in skus:
        cost_key = f"{role}_cost"
        formula[cost_key] = f"{role} * skus.{role}.unit_price_usd"
        cost_terms.append(cost_key)
    formula["total"] = " + ".join(cost_terms)
    return formula


def _is_service_specific_formula(formula: dict[str, str]) -> bool:
    return any(marker in formula for marker in SERVICE_FORMULA_MARKERS)


def _roles_referenced_in_formula(formula: dict[str, str]) -> list[str]:
    roles: list[str] = []
    seen: set[str] = set()
    for expression in formula.values():
        for token in expression.replace("(", " ").replace(")", " ").split():
            if not token.startswith("skus."):
                continue
            role = token.removeprefix("skus.").split(".", 1)[0]
            if role and role not in seen:
                seen.add(role)
                roles.append(role)
    return roles


def _best_role_for_category(
    skus: dict[str, dict[str, Any]],
    keywords: tuple[str, ...],
) -> str | None:
    matches: list[str] = []
    for role, sku in skus.items():
        if _should_skip_role(role, sku):
            continue
        haystack = " ".join(
            [
                role,
                str(sku.get("description", "")),
                str(sku.get("usage_unit", "")),
            ]
        ).lower()
        if any(keyword in haystack for keyword in keywords):
            matches.append(role)

    if not matches:
        return None

    return min(matches, key=lambda role: float(skus[role].get("unit_price_usd", 0.0)))


def _should_skip_role(role: str, sku: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            role,
            str(sku.get("description", "")),
            str(sku.get("usage_unit", "")),
        ]
    ).lower()
    return any(keyword in haystack for keyword in SKIP_ROLE_KEYWORDS)
