"""Select Firestore SKUs and build formulas from component profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config.params import STAGE_PRODUCTION
from app.schemas.domain import RequirementContext
from app.services.pricing.component_profiles import (
    ComponentProfile,
    FormulaKind,
    PricingRole,
)
from app.services.pricing.sku_classifier import iter_skus_for_role
from app.services.pricing.usage_profile import USER_COUNT_MAP, UsageProfile

HOURS_PER_MONTH = 730.0

FALLBACK_API_PRICE_PER_MILLION = 3.0
FALLBACK_QUEUE_PRICE_PER_MILLION = 0.40

INSTANCE_SKIP = (
    "multi_az", "mirror", "extendedsupport", "outpost", "syncdurability",
    "metal", "24xl", "16xl", "12xl", "48xl", "32xl", "8xl",
)

ROLE_SLOT: dict[PricingRole, str] = {
    PricingRole.CPU: "cpu",
    PricingRole.MEMORY: "memory",
    PricingRole.REQUESTS: "requests",
    PricingRole.EGRESS: "egress",
    PricingRole.DATA_TRANSFER: "egress",
    PricingRole.STORAGE: "storage",
    PricingRole.READ_OPERATIONS: "read_ops",
    PricingRole.WRITE_OPERATIONS: "write_ops",
    PricingRole.INSTANCE: "instance",
    PricingRole.CACHE_INSTANCE: "instance",
    PricingRole.GATEWAY_CAPACITY: "instance",
    PricingRole.GB_SECONDS: "execution",
    PricingRole.EXECUTION: "execution",
    PricingRole.MAU: "auth_mau",
    PricingRole.AUTH_EVENTS: "auth_events",
    PricingRole.SMS_MFA: "sms",
    PricingRole.INPUT_TOKENS: "input_tokens",
    PricingRole.OUTPUT_TOKENS: "output_tokens",
    PricingRole.INFERENCE: "inference",
    PricingRole.HOSTING: "hosting",
    PricingRole.COMPUTE: "compute",
    PricingRole.QUEUE_MESSAGES: "requests",
    PricingRole.LOG_INGESTION: "requests",
    PricingRole.BACKUP: "backup",
}

SLOT_TERM_CANDIDATES: dict[str, tuple[str, ...]] = {
    "cpu": ("cpu_cost", "vcpu_cost"),
    "memory": ("memory_cost",),
    "requests": ("request_cost", "ingestion_cost"),
    "egress": ("egress_cost",),
    "read_ops": ("read_cost",),
    "write_ops": ("write_cost",),
    "instance": ("instance_cost",),
    "execution": ("duration_cost", "execution_cost"),
    "storage": ("storage_cost",),
    "auth_mau": ("auth_cost",),
    "auth_events": ("auth_cost",),
    "sms": ("sms_cost",),
    "input_tokens": ("input_cost",),
    "output_tokens": ("output_cost",),
    "inference": ("inference_cost",),
    "hosting": ("hosting_cost",),
    "compute": ("compute_cost",),
    "backup": ("backup_cost",),
}


@dataclass
class SkuSelectionAudit:
    profile_name: str
    formula: str
    required_roles: list[str]
    optional_roles: list[str]
    forbidden_roles: list[str]
    roles_considered: list[str] = field(default_factory=list)
    skipped_optional_roles: list[dict[str, str]] = field(default_factory=list)
    selected: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, str]] = field(default_factory=list)
    missing_required_roles: list[str] = field(default_factory=list)
    formula_expression: str = ""
    role_usage: dict[str, float] = field(default_factory=dict)
    role_costs: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile_name,
            "formula": self.formula,
            "required_roles": self.required_roles,
            "optional_roles": self.optional_roles,
            "forbidden_roles": self.forbidden_roles,
            "roles_considered": self.roles_considered,
            "skipped_optional_roles": self.skipped_optional_roles,
            "selected": self.selected,
            "rejected": self.rejected,
            "missing_required_roles": self.missing_required_roles,
            "formula_expression": self.formula_expression,
            "role_usage": self.role_usage,
            "role_costs": self.role_costs,
        }


class ComponentModelPlan:
    __slots__ = (
        "skus",
        "formula",
        "usage_overrides",
        "selection_notes",
        "profile",
        "role_skus",
        "audit",
        "profile_resolution",
    )

    def __init__(
        self,
        skus: dict[str, dict[str, Any]],
        formula: dict[str, str],
        usage_overrides: dict[str, float] | None = None,
        selection_notes: list[str] | None = None,
        profile: ComponentProfile | None = None,
        role_skus: dict[PricingRole, dict[str, Any]] | None = None,
        audit: SkuSelectionAudit | None = None,
        profile_resolution: Any | None = None,
    ) -> None:
        self.skus = skus
        self.formula = formula
        self.usage_overrides = usage_overrides or {}
        self.selection_notes = selection_notes or []
        self.profile = profile
        self.role_skus = role_skus or {}
        self.audit = audit
        self.profile_resolution = profile_resolution


def build_plan_from_profile(
    *,
    comp_profile: ComponentProfile,
    skus: dict[str, dict[str, Any]],
    usage: UsageProfile,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
) -> ComponentModelPlan:
    """Search Firestore catalog for best SKU per profile role, then apply profile formula."""
    notes: list[str] = []
    audit = _new_audit(comp_profile)
    role_skus = select_role_skus(
        comp_profile,
        skus,
        notes,
        audit=audit,
        stage=stage,
        expected_users=expected_users,
        requirements=requirements,
    )

    missing_required = [
        role.value
        for role in comp_profile.required_roles
        if role not in role_skus
    ]
    audit.missing_required_roles = missing_required
    for role_value in missing_required:
        notes.append(f"Missing required role {role_value}; estimate uses partial SKU set.")

    usage_overrides: dict[str, float] = {}

    if comp_profile.formula == FormulaKind.CDN:
        usage_overrides.update(_cdn_usage_overrides(expected_users, stage, requirements))
    elif comp_profile.formula == FormulaKind.MONITORING:
        users = USER_COUNT_MAP.get(expected_users, 1_000)
        usage_overrides["log_ingestion_gb"] = max(1.0, users * 0.001)
        notes.append(f"Assumed {usage_overrides['log_ingestion_gb']:.1f} GiB log/metric ingestion per month.")

    if comp_profile.formula == FormulaKind.GATEWAY and PricingRole.GATEWAY_CAPACITY in role_skus:
        units = 1.0 if stage != STAGE_PRODUCTION else 2.0
        usage_overrides["gateway_units"] = units
        notes.append(f"API gateway sized at {units:g} capacity unit(s).")

    instance_sku = role_skus.get(PricingRole.INSTANCE) or role_skus.get(PricingRole.CACHE_INSTANCE)
    if instance_sku:
        usage_overrides.update(_instance_usage_overrides(instance_sku))

    selected = {ROLE_SLOT[role]: sku for role, sku in role_skus.items()}
    formula = build_formula(comp_profile.formula, selected, role_skus, notes)
    audit.formula_expression = formula.get("total", "0")
    audit.selected = [
        {
            "pricing_role": role.value,
            "slot": ROLE_SLOT[role],
            "catalog_role": str(sku.get("_source_role", "")),
            "sku_id": str(sku.get("sku_id", ROLE_SLOT[role])),
            "unit_price_usd": float(sku.get("unit_price_usd", 0.0) or 0.0),
        }
        for role, sku in role_skus.items()
    ]

    return ComponentModelPlan(
        selected,
        formula,
        usage_overrides,
        notes,
        comp_profile,
        role_skus,
        audit,
    )


def populate_audit_usage_and_costs(
    audit: SkuSelectionAudit,
    *,
    role_skus: dict[PricingRole, dict[str, Any]],
    usage: dict[str, float],
    term_costs: dict[str, float],
) -> None:
    from app.services.pricing.usage_profile import ROLE_USAGE_VARIABLE

    for role, sku in role_skus.items():
        slot = ROLE_SLOT[role]
        variable = ROLE_USAGE_VARIABLE.get(slot, slot)
        quantity = usage.get(variable, usage.get(slot, 0.0))
        audit.role_usage[role.value] = round(float(quantity), 4)

        cost = term_cost_for_slot(slot, term_costs)
        if cost is not None:
            audit.role_costs[role.value] = round(max(0.0, cost), 4)


def term_cost_for_slot(slot: str, term_costs: dict[str, float]) -> float | None:
    for key in SLOT_TERM_CANDIDATES.get(slot, (f"{slot}_cost",)):
        if key in term_costs:
            return term_costs[key]
    return None


def _new_audit(comp_profile: ComponentProfile) -> SkuSelectionAudit:
    return SkuSelectionAudit(
        profile_name=comp_profile.name,
        formula=comp_profile.formula.value,
        required_roles=sorted(role.value for role in comp_profile.required_roles),
        optional_roles=sorted(role.value for role in comp_profile.optional_roles),
        forbidden_roles=sorted(role.value for role in comp_profile.forbidden_roles),
    )


def optional_role_applies(
    role: PricingRole,
    comp_profile: ComponentProfile,
    *,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
) -> bool:
    if comp_profile.is_required(role):
        return True

    if role == PricingRole.EGRESS:
        if comp_profile.formula in (FormulaKind.CDN, FormulaKind.LOAD_BALANCER):
            return True
        return bool(requirements.file_upload or requirements.ai)

    if role == PricingRole.BACKUP:
        return stage == STAGE_PRODUCTION

    if role == PricingRole.SMS_MFA:
        return requirements.auth

    if role == PricingRole.GATEWAY_CAPACITY:
        users = USER_COUNT_MAP.get(expected_users, 1_000)
        return stage == STAGE_PRODUCTION or users >= 10_000

    if role == PricingRole.INFERENCE:
        return False

    if role == PricingRole.REQUESTS and comp_profile.formula == FormulaKind.AI:
        return requirements.ai

    if role == PricingRole.COMPUTE:
        return False

    if role == PricingRole.DATA_TRANSFER:
        return False

    return True


def select_role_skus(
    comp_profile: ComponentProfile,
    skus: dict[str, dict[str, Any]],
    notes: list[str],
    *,
    audit: SkuSelectionAudit,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
) -> dict[PricingRole, dict[str, Any]]:
    """Pick at most one catalog SKU per pricing role, respecting profile constraints."""
    selected: dict[PricingRole, dict[str, Any]] = {}
    handled_groups: set[frozenset[PricingRole]] = set()

    role_order = _role_pick_order(comp_profile, stage, expected_users, requirements, audit)

    for role in role_order:
        group = comp_profile.exclusive_group_for(role)
        if group is not None:
            if group in handled_groups:
                continue
            handled_groups.add(group)
            group_roles = [r for r in role_order if r in group]
            picked = _pick_first_available(
                comp_profile,
                skus,
                group_roles,
                notes,
                audit,
                stage,
                expected_users,
                requirements,
            )
            if picked:
                selected[picked[0]] = picked[1]
            continue

        if role in selected:
            continue
        sku = _pick_role_sku(
            comp_profile,
            skus,
            role,
            notes,
            audit,
            stage,
            expected_users,
            requirements,
        )
        if sku:
            selected[role] = sku

    if comp_profile.formula.value == "ai":
        has_tokens = PricingRole.INPUT_TOKENS in selected or PricingRole.OUTPUT_TOKENS in selected
        if not has_tokens and PricingRole.INFERENCE not in selected:
            inf = _pick_role_sku(
                comp_profile,
                skus,
                PricingRole.INFERENCE,
                notes,
                audit,
                stage,
                expected_users,
                requirements,
                force=True,
            )
            if inf:
                selected[PricingRole.INFERENCE] = inf
                notes.append("AI fallback: using inference SKU (no token SKUs found).")

    return selected


def _role_pick_order(
    comp_profile: ComponentProfile,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
    audit: SkuSelectionAudit,
) -> list[PricingRole]:
    required = list(comp_profile.required_roles)
    optional: list[PricingRole] = []

    for role in comp_profile.optional_roles:
        if optional_role_applies(role, comp_profile, stage=stage, expected_users=expected_users, requirements=requirements):
            optional.append(role)
        else:
            audit.skipped_optional_roles.append(
                {
                    "role": role.value,
                    "reason": "optional role not implied by requirements or formula",
                }
            )

    if PricingRole.GATEWAY_CAPACITY in optional:
        users = USER_COUNT_MAP.get(expected_users, 1_000)
        if stage == STAGE_PRODUCTION or users >= 10_000:
            optional = [PricingRole.GATEWAY_CAPACITY] + [
                r for r in optional if r != PricingRole.GATEWAY_CAPACITY
            ]

    order = required + optional
    audit.roles_considered = [role.value for role in order]
    return order


def _pick_first_available(
    comp_profile: ComponentProfile,
    skus: dict[str, dict[str, Any]],
    roles: list[PricingRole],
    notes: list[str],
    audit: SkuSelectionAudit,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
) -> tuple[PricingRole, dict[str, Any]] | None:
    for role in roles:
        sku = _pick_role_sku(
            comp_profile,
            skus,
            role,
            notes,
            audit,
            stage,
            expected_users,
            requirements,
        )
        if sku:
            notes.append(f"Exclusive group: using {role.value}, skipping peers.")
            return role, sku
    return None


def _pick_role_sku(
    comp_profile: ComponentProfile,
    skus: dict[str, dict[str, Any]],
    role: PricingRole,
    notes: list[str],
    audit: SkuSelectionAudit,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
    *,
    force: bool = False,
) -> dict[str, Any] | None:
    if not comp_profile.allows(role):
        return None

    if not force and role in comp_profile.optional_roles and not optional_role_applies(
        role,
        comp_profile,
        stage=stage,
        expected_users=expected_users,
        requirements=requirements,
    ):
        return None

    if role in (PricingRole.INSTANCE, PricingRole.CACHE_INSTANCE):
        return _pick_tiered_sku(comp_profile, skus, role, stage, expected_users, notes, audit)

    allow_zero = role in (
        PricingRole.READ_OPERATIONS,
        PricingRole.WRITE_OPERATIONS,
        PricingRole.REQUESTS,
        PricingRole.EXECUTION,
        PricingRole.QUEUE_MESSAGES,
        PricingRole.STORAGE,
        PricingRole.HOSTING,
        PricingRole.EGRESS,
    )
    reject_log: list[dict[str, str]] = []
    candidates = iter_skus_for_role(skus, comp_profile, role, reject_log=reject_log)
    audit.rejected.extend(reject_log)

    best_catalog_role: str | None = None
    best_sku: dict[str, Any] | None = None
    best_price = float("inf") if not allow_zero else -1.0

    for catalog_role, sku in candidates:
        price = float(sku.get("unit_price_usd", 0.0) or 0.0)
        if price <= 0.0 and not allow_zero:
            continue
        if allow_zero:
            if best_sku is None or price > best_price:
                best_catalog_role, best_sku, best_price = catalog_role, sku, price
        elif price < best_price:
            best_catalog_role, best_sku, best_price = catalog_role, sku, price

    if best_catalog_role and best_sku is not None:
        notes.append(f"Selected {role.value} SKU from catalog role '{best_catalog_role}'.")
        return {
            **best_sku,
            "_source_role": best_catalog_role,
            "_pricing_role": role.value,
        }

    if comp_profile.is_required(role):
        notes.append(f"No Firestore SKU matched required role {role.value}.")
    return None


def _pick_tiered_sku(
    comp_profile: ComponentProfile,
    skus: dict[str, dict[str, Any]],
    role: PricingRole,
    stage: str,
    expected_users: str,
    notes: list[str],
    audit: SkuSelectionAudit,
) -> dict[str, Any] | None:
    target = _target_instance_tier(stage, expected_users, comp_profile)
    reject_log: list[dict[str, str]] = []
    candidates = iter_skus_for_role(skus, comp_profile, role, reject_log=reject_log)
    audit.rejected.extend(reject_log)

    skip_tokens = INSTANCE_SKIP
    if role == PricingRole.CACHE_INSTANCE:
        skip_tokens = skip_tokens + (
            "premium", "enterprise", "p1", "p2", "p3", "p4", "p5",
            "xlarge", "e5", "e10", "e20", "e50", "e100",
        )

    best: tuple[str, dict[str, Any]] | None = None
    best_distance = 10_000.0
    best_price = 10_000_000.0

    for catalog_role, sku in candidates:
        haystack = _haystack(catalog_role, sku)
        if _contains(haystack, skip_tokens):
            audit.rejected.append(
                {
                    "catalog_role": catalog_role,
                    "sku_id": str(sku.get("sku_id", catalog_role)),
                    "target_role": role.value,
                    "reason": "oversized or unsupported instance tier",
                }
            )
            continue
        price = float(sku.get("unit_price_usd", 0.0) or 0.0)
        if price <= 0.0:
            continue
        tier = _instance_tier_score(catalog_role, sku) if role == PricingRole.INSTANCE else _cache_tier_score(
            catalog_role, sku
        )
        distance = abs(tier - target)
        if distance < best_distance or (distance == best_distance and price < best_price):
            best_distance, best_price, best = distance, price, (catalog_role, sku)

    if best is None:
        if comp_profile.is_required(role):
            notes.append(f"No Firestore SKU matched required role {role.value}.")
        return None
    catalog_role, sku = best
    notes.append(f"Selected {role.value} SKU '{catalog_role}' (tier target {target}).")
    return {**sku, "_source_role": catalog_role, "_pricing_role": role.value}


def build_formula(
    kind: FormulaKind,
    selected: dict[str, dict[str, Any]],
    role_skus: dict[PricingRole, dict[str, Any]],
    notes: list[str],
) -> dict[str, str]:
    builders = {
        FormulaKind.CLOUD_RUN: _formula_cloud_run,
        FormulaKind.LAMBDA: _formula_lambda,
        FormulaKind.AZURE_FUNCTIONS: _formula_azure_functions,
        FormulaKind.ECS_FARGATE: _formula_ecs_fargate,
        FormulaKind.CONTAINER_APPS: _formula_cloud_run,
        FormulaKind.REQUESTS_ONLY: _formula_requests_only,
        FormulaKind.GATEWAY: _formula_gateway,
        FormulaKind.OBJECT_STORAGE: _formula_object_storage,
        FormulaKind.DATABASE: _formula_database,
        FormulaKind.DATABASE_NOSQL: _formula_database_nosql,
        FormulaKind.CACHE: _formula_cache,
        FormulaKind.AUTH: _formula_auth,
        FormulaKind.AI: _formula_ai,
        FormulaKind.CDN: _formula_cdn,
        FormulaKind.HOSTING: _formula_hosting,
        FormulaKind.QUEUE: _formula_queue,
        FormulaKind.MONITORING: _formula_monitoring,
        FormulaKind.LOAD_BALANCER: _formula_cdn,
        FormulaKind.GENERIC: _formula_generic,
    }
    builder = builders.get(kind, _formula_generic)
    formula = builder(selected, role_skus)
    if formula.get("total") == "0" and kind == FormulaKind.REQUESTS_ONLY:
        notes.append(f"Fallback ${FALLBACK_API_PRICE_PER_MILLION:.2f}/M requests (no catalog SKU).")
        selected["requests"] = _fallback_sku(FALLBACK_API_PRICE_PER_MILLION, PricingRole.REQUESTS)
        return _formula_requests_only(selected, role_skus)
    if formula.get("total") == "0" and kind == FormulaKind.QUEUE:
        notes.append(f"Fallback ${FALLBACK_QUEUE_PRICE_PER_MILLION:.2f}/M messages.")
        selected["requests"] = _fallback_sku(FALLBACK_QUEUE_PRICE_PER_MILLION, PricingRole.QUEUE_MESSAGES)
        return _formula_queue(selected, role_skus)
    return formula


def _formula_cloud_run(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "cpu" in selected:
        f["cpu_cost"] = "monthly_vcpu_hours * skus.cpu.unit_price_usd"
        terms.append("cpu_cost")
    if "memory" in selected:
        f["memory_cost"] = "monthly_memory_gib_hours * skus.memory.unit_price_usd"
        terms.append("memory_cost")
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    if "egress" in selected:
        f["egress_cost"] = "egress_gb * skus.egress.unit_price_usd"
        terms.append("egress_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_lambda(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    if "execution" in selected:
        f["duration_cost"] = "monthly_gb_seconds * skus.execution.unit_price_usd"
        terms.append("duration_cost")
    if "egress" in selected:
        f["egress_cost"] = "egress_gb * skus.egress.unit_price_usd"
        terms.append("egress_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_azure_functions(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "execution" in selected:
        f["execution_cost"] = "monthly_executions * skus.execution.unit_price_usd"
        terms.append("execution_cost")
    if "cpu" in selected:
        f["vcpu_cost"] = "monthly_vcpu_hours * skus.cpu.unit_price_usd"
        terms.append("vcpu_cost")
    if "memory" in selected:
        f["memory_cost"] = "monthly_memory_gib_hours * skus.memory.unit_price_usd"
        terms.append("memory_cost")
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_ecs_fargate(selected: dict, _role_skus: dict) -> dict[str, str]:
    return _formula_cloud_run(selected, _role_skus)


def _formula_requests_only(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "requests" not in selected:
        return {"total": "0"}
    return {
        "request_cost": _req_expr("requests", selected["requests"]),
        "total": "request_cost",
    }


def _formula_gateway(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "instance" in selected:
        return {
            "instance_cost": "gateway_units * instance_billable_units * skus.instance.unit_price_usd",
            "total": "instance_cost",
        }
    return _formula_requests_only(selected, _role_skus)


def _formula_object_storage(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "storage" in selected:
        f["storage_cost"] = "storage_gib * skus.storage.unit_price_usd"
        terms.append("storage_cost")
    if "read_ops" in selected:
        f["read_cost"] = "monthly_requests * skus.read_ops.unit_price_usd"
        terms.append("read_cost")
    if "write_ops" in selected:
        f["write_cost"] = "monthly_requests * skus.write_ops.unit_price_usd"
        terms.append("write_cost")
    if "egress" in selected:
        f["egress_cost"] = "egress_gb * skus.egress.unit_price_usd"
        terms.append("egress_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_database(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "instance" in selected:
        f["instance_cost"] = "instance_billable_units * skus.instance.unit_price_usd"
        terms.append("instance_cost")
    if "storage" in selected:
        f["storage_cost"] = "storage_gib * skus.storage.unit_price_usd"
        terms.append("storage_cost")
    if "read_ops" in selected:
        f["read_cost"] = "monthly_requests * skus.read_ops.unit_price_usd"
        terms.append("read_cost")
    if "write_ops" in selected:
        f["write_cost"] = "monthly_requests * skus.write_ops.unit_price_usd"
        terms.append("write_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_database_nosql(selected: dict, role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "read_ops" in selected:
        f["read_cost"] = "monthly_requests * skus.read_ops.unit_price_usd"
        terms.append("read_cost")
    elif "write_ops" in selected:
        f["write_cost"] = "monthly_requests * skus.write_ops.unit_price_usd"
        terms.append("write_cost")
    elif "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    if "storage" in selected:
        f["storage_cost"] = "storage_gib * skus.storage.unit_price_usd"
        terms.append("storage_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_cache(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "instance" not in selected:
        return {"total": "0"}
    return {
        "instance_cost": "instance_billable_units * skus.instance.unit_price_usd",
        "total": "instance_cost",
    }


def _formula_auth(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "auth_mau" in selected:
        return {
            "auth_cost": _auth_expr("auth_mau", selected["auth_mau"]),
            "total": "auth_cost",
        }
    if "auth_events" in selected:
        return {
            "auth_cost": _auth_expr("auth_events", selected["auth_events"]),
            "total": "auth_cost",
        }
    return {"total": "0"}


def _formula_ai(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    for slot, term in (
        ("input_tokens", "input_cost"),
        ("output_tokens", "output_cost"),
        ("inference", "inference_cost"),
    ):
        if slot in selected:
            f[term] = _token_expr(slot, selected[slot])
            terms.append(term)
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_cdn(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "egress" not in selected:
        return {"total": "0"}
    return {"egress_cost": "egress_gb * skus.egress.unit_price_usd", "total": "egress_cost"}


def _formula_hosting(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    for slot, var in (("hosting", "hosting_cost"), ("compute", "compute_cost"), ("storage", "storage_cost")):
        if slot in selected:
            if slot == "storage":
                f[var] = "storage_gib * skus.storage.unit_price_usd"
            else:
                f[var] = _req_expr(slot, selected[slot])
            terms.append(var)
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _formula_queue(selected: dict, _role_skus: dict) -> dict[str, str]:
    return _formula_requests_only(selected, _role_skus)


def _formula_monitoring(selected: dict, _role_skus: dict) -> dict[str, str]:
    if "requests" not in selected:
        return {"total": "0"}
    return {
        "ingestion_cost": "log_ingestion_gb * skus.requests.unit_price_usd",
        "total": "ingestion_cost",
    }


def _formula_generic(selected: dict, _role_skus: dict) -> dict[str, str]:
    terms: list[str] = []
    f: dict[str, str] = {"total": "0"}
    if "requests" in selected:
        f["request_cost"] = _req_expr("requests", selected["requests"])
        terms.append("request_cost")
    if "storage" in selected:
        f["storage_cost"] = "storage_gib * skus.storage.unit_price_usd"
        terms.append("storage_cost")
    f["total"] = " + ".join(terms) if terms else "0"
    return f


def _cdn_usage_overrides(
    expected_users: str,
    stage: str,
    requirements: RequirementContext,
) -> dict[str, float]:
    users = USER_COUNT_MAP.get(expected_users, 1_000)
    gb_per_user = 0.3 if (requirements.file_upload or requirements.ai) else 0.03
    if stage == STAGE_PRODUCTION:
        gb_per_user *= 1.5
    return {"egress_gb": users * gb_per_user}


def _fallback_sku(price_per_million: float, role: PricingRole) -> dict[str, Any]:
    return {
        "sku_id": "fallback-pricing",
        "description": f"Fallback {role.value} pricing",
        "usage_unit": "1M units",
        "unit_price_usd": price_per_million,
        "_source_role": "fallback",
        "_pricing_role": role.value,
    }


def _instance_usage_overrides(sku: dict[str, Any]) -> dict[str, float]:
    usage_unit = str(sku.get("usage_unit", "")).lower()
    if "day" in usage_unit:
        return {"instance_billable_units": 30.0}
    if "month" in usage_unit or usage_unit.endswith("mo"):
        return {"instance_billable_units": 1.0}
    return {"instance_billable_units": HOURS_PER_MONTH}


def _target_instance_tier(
    stage: str,
    expected_users: str,
    comp_profile: ComponentProfile | None = None,
) -> int:
    if comp_profile is not None and comp_profile.default_tier_by_stage:
        if stage in comp_profile.default_tier_by_stage:
            return comp_profile.default_tier_by_stage[stage]
    users = USER_COUNT_MAP.get(expected_users, 1_000)
    if stage == STAGE_PRODUCTION or users >= 10_000:
        return 4
    if users >= 1_000:
        return 3
    return 2


def _instance_tier_score(role: str, sku: dict[str, Any]) -> int:
    haystack = _haystack(role, sku)
    if _contains(haystack, ("metal", "24xl", "16xl", "12xl", "48xl", "32xl")):
        return 100
    if _contains(haystack, ("s4", "s3", "p2", "p1")):
        return 6
    if _contains(haystack, ("s2", "s1", "gp2", "medium")):
        return 4
    if _contains(haystack, ("s0", "b1", "basic", "micro", "t4g.micro", "small")):
        return 2
    if "xlarge" in haystack:
        return 5
    return 50


def _cache_tier_score(role: str, sku: dict[str, Any]) -> int:
    haystack = _haystack(role, sku)
    if _contains(haystack, ("c0", "basic", "micro", "nano")):
        return 1
    if _contains(haystack, ("c1", "small", "standard")):
        return 2
    if _contains(haystack, ("c2", "medium")):
        return 3
    return _instance_tier_score(role, sku)


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


def _request_divisor(sku: dict[str, Any]) -> float:
    haystack = _haystack("_", sku)
    if _contains(haystack, ("million", "1m", "per m", "/m ", "1/m")):
        return 1_000_000.0
    if _contains(haystack, ("100k", "100,000", "100000")):
        return 100_000.0
    return 1.0


def _token_divisor(sku: dict[str, Any]) -> float:
    usage_unit = str(sku.get("usage_unit", "")).lower()
    haystack = _haystack("_", sku)
    if usage_unit in {"1m", "m"} or "million" in haystack:
        return 1_000_000.0
    if usage_unit in {"1k", "k"} or "per 1k" in haystack:
        return 1_000.0
    price = float(sku.get("unit_price_usd", 0.0) or 0.0)
    if price < 1.0 and any(token in usage_unit for token in ("count", "token", "unit")):
        return 1_000_000.0
    return 1_000.0


def _req_expr(slot: str, sku: dict[str, Any]) -> str:
    d = _request_divisor(sku)
    if d > 1.0:
        return f"(monthly_requests / {int(d)}) * skus.{slot}.unit_price_usd"
    return f"monthly_requests * skus.{slot}.unit_price_usd"


def _auth_expr(slot: str, sku: dict[str, Any]) -> str:
    d = _request_divisor(sku)
    if d > 1.0:
        return f"(monthly_auth_events / {int(d)}) * skus.{slot}.unit_price_usd"
    return f"monthly_auth_events * skus.{slot}.unit_price_usd"


def _token_expr(slot: str, sku: dict[str, Any]) -> str:
    d = _token_divisor(sku)
    return f"(monthly_tokens / {int(d)}) * skus.{slot}.unit_price_usd"
