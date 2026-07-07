"""Entity- and category-based storage inference from LLM storage models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.exceptions import AIValidationError
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption

_KB_PER_GB = 1024 * 1024
_RDS_INDEX_OVERHEAD = 1.15

RDS_ENTITY_SUGGESTIONS = (
    "user_profile",
    "settings_preferences",
    "application_records",
    "history_events",
    "orders_products",
    "messages_transcripts",
    "recommendations_metadata",
    "audit_logs",
)

S3_CATEGORY_SUGGESTIONS = (
    "static_assets",
    "user_uploads",
    "generated_files",
    "media_documents",
    "exports_backups",
)


@dataclass(frozen=True)
class RdsEntityStorage:
    entity: str
    records_per_user_per_month: float
    average_record_size_kb: float
    retention_months: float
    storage_gb_per_user: float
    reasoning: str


@dataclass(frozen=True)
class S3CategoryStorage:
    category: str
    scaling: str  # "static" | "per_user"
    storage_gb: float  # total for static, per-user for per_user categories
    writes_per_user_per_month: float
    reads_per_user_per_month: float
    average_object_size_kb: float
    reasoning: str


@dataclass(frozen=True)
class RdsStorageDerivation:
    storage_gb_per_user: float
    backup_storage_gb_per_user: float
    backup_retention_days: int
    entities: tuple[RdsEntityStorage, ...]


@dataclass(frozen=True)
class S3StorageDerivation:
    static_storage_gb: float
    storage_gb_per_user: float
    writes_per_user_per_month: float
    reads_per_user_per_month: float
    avg_download_size_kb: float
    categories: tuple[S3CategoryStorage, ...]


def entity_storage_gb_per_user(
    *,
    records_per_user_per_month: float,
    average_record_size_kb: float,
    retention_months: float,
    index_overhead: float = _RDS_INDEX_OVERHEAD,
) -> float:
    """Compute GB per user for one logical entity."""
    records = max(0.0, float(records_per_user_per_month))
    size_kb = max(0.01, float(average_record_size_kb))
    retention = max(0.1, float(retention_months))

    if records <= 1.0:
        active_records = records
    else:
        active_records = records * retention

    raw_gb = active_records * size_kb * 1024 / (_KB_PER_GB * 1024)
    return round(raw_gb * index_overhead, 8)


def backup_storage_gb_per_user(
    database_storage_gb_per_user: float,
    *,
    backup_retention_days: int,
) -> float:
    """Derive backup GB/user from database size and retention (not independent guess)."""
    days = max(1, int(backup_retention_days))
    # Approximate average retained backup footprint as one rolling snapshot
    # scaled by retention window (7-day MVP ≈ 23% of DB size).
    factor = min(1.0, days / 30.0)
    return round(max(0.0, database_storage_gb_per_user) * factor, 8)


def parse_rds_storage_model(
    storage_model: Any,
    *,
    component_id: str,
) -> RdsStorageDerivation:
    if not isinstance(storage_model, dict):
        raise AIValidationError(
            f"Component {component_id}: storage_model must be an object for database components."
        )

    entities_raw = storage_model.get("entities")
    if not isinstance(entities_raw, list) or not entities_raw:
        raise AIValidationError(
            f"Component {component_id}: storage_model.entities must be a non-empty array."
        )

    backup_retention_days = storage_model.get("backup_retention_days", 7)
    if not isinstance(backup_retention_days, (int, float)) or backup_retention_days <= 0:
        raise AIValidationError(
            f"Component {component_id}: storage_model.backup_retention_days must be a positive number."
        )
    backup_retention_days = int(backup_retention_days)

    entities: list[RdsEntityStorage] = []
    for idx, item in enumerate(entities_raw):
        if not isinstance(item, dict):
            raise AIValidationError(
                f"Component {component_id}: storage_model.entities[{idx}] must be an object."
            )
        entity_name = item.get("entity")
        if not entity_name or not isinstance(entity_name, str):
            raise AIValidationError(
                f"Component {component_id}: entity[{idx}] requires non-empty entity name."
            )
        reasoning = item.get("reasoning")
        if not reasoning or not isinstance(reasoning, str) or not reasoning.strip():
            raise AIValidationError(
                f"Component {component_id}: entity {entity_name!r} requires non-empty reasoning."
            )

        for field in (
            "records_per_user_per_month",
            "average_record_size_kb",
            "retention_months",
        ):
            if field not in item:
                raise AIValidationError(
                    f"Component {component_id}: entity {entity_name!r} missing {field}."
                )

        records = float(item["records_per_user_per_month"])
        size_kb = float(item["average_record_size_kb"])
        retention = float(item["retention_months"])
        if records < 0 or size_kb <= 0 or retention <= 0:
            raise AIValidationError(
                f"Component {component_id}: entity {entity_name!r} has invalid numeric fields."
            )

        per_user = entity_storage_gb_per_user(
            records_per_user_per_month=records,
            average_record_size_kb=size_kb,
            retention_months=retention,
        )
        entities.append(
            RdsEntityStorage(
                entity=entity_name.strip(),
                records_per_user_per_month=records,
                average_record_size_kb=size_kb,
                retention_months=retention,
                storage_gb_per_user=per_user,
                reasoning=reasoning.strip(),
            )
        )

    total_per_user = round(sum(e.storage_gb_per_user for e in entities), 8)
    backup_per_user = backup_storage_gb_per_user(
        total_per_user,
        backup_retention_days=backup_retention_days,
    )
    return RdsStorageDerivation(
        storage_gb_per_user=max(total_per_user, 0.0001),
        backup_storage_gb_per_user=backup_per_user,
        backup_retention_days=backup_retention_days,
        entities=tuple(entities),
    )


def parse_s3_storage_model(
    storage_model: Any,
    *,
    component_id: str,
    file_upload: bool,
) -> S3StorageDerivation:
    if not isinstance(storage_model, dict):
        raise AIValidationError(
            f"Component {component_id}: storage_model must be an object for object storage."
        )

    categories_raw = storage_model.get("categories")
    if not isinstance(categories_raw, list) or not categories_raw:
        raise AIValidationError(
            f"Component {component_id}: storage_model.categories must be a non-empty array."
        )

    categories: list[S3CategoryStorage] = []
    static_total = 0.0
    per_user_total = 0.0
    writes_per_user = 0.0
    reads_per_user = 0.0
    weighted_download_kb = 0.0
    read_weight = 0.0

    for idx, item in enumerate(categories_raw):
        if not isinstance(item, dict):
            raise AIValidationError(
                f"Component {component_id}: storage_model.categories[{idx}] must be an object."
            )
        category = item.get("category")
        if not category or not isinstance(category, str):
            raise AIValidationError(
                f"Component {component_id}: categories[{idx}] requires category name."
            )
        reasoning = item.get("reasoning")
        if not reasoning or not isinstance(reasoning, str) or not reasoning.strip():
            raise AIValidationError(
                f"Component {component_id}: category {category!r} requires non-empty reasoning."
            )

        scaling = str(item.get("scaling", "per_user")).strip().lower()
        if scaling not in {"static", "per_user"}:
            raise AIValidationError(
                f"Component {component_id}: category {category!r} scaling must be static or per_user."
            )

        writes = float(item.get("writes_per_user_per_month", 0))
        reads = float(item.get("reads_per_user_per_month", 0))
        avg_kb = float(item.get("average_object_size_kb", 64))

        upload_categories = {"user_uploads", "media_documents"}
        if not file_upload and category in upload_categories:
            writes = reads = 0.0
            avg_kb = max(avg_kb, 1.0)
            if scaling == "per_user":
                item = {**item, "storage_gb_per_user": 0.0}
            else:
                item = {**item, "total_storage_gb": 0.0}

        if writes < 0 or reads < 0:
            raise AIValidationError(
                f"Component {component_id}: category {category!r} has invalid operation counts."
            )
        if avg_kb <= 0:
            avg_kb = 1.0 if (writes > 0 or reads > 0) else 64.0

        if scaling == "static":
            total_gb = float(item.get("total_storage_gb", 0))
            if total_gb < 0:
                raise AIValidationError(
                    f"Component {component_id}: static category {category!r} needs total_storage_gb >= 0."
                )
            static_total += total_gb
            storage_gb = total_gb
        else:
            if "storage_gb_per_user" in item:
                per_user_gb = float(item["storage_gb_per_user"])
            else:
                records = float(item.get("records_per_user_per_month", 0))
                retention = float(item.get("retention_months", 12))
                per_user_gb = entity_storage_gb_per_user(
                    records_per_user_per_month=records,
                    average_record_size_kb=avg_kb,
                    retention_months=retention,
                    index_overhead=1.0,
                )
            if per_user_gb < 0:
                raise AIValidationError(
                    f"Component {component_id}: per_user category {category!r} has negative storage."
                )
            per_user_total += per_user_gb
            storage_gb = per_user_gb

        categories.append(
            S3CategoryStorage(
                category=category.strip(),
                scaling=scaling,
                storage_gb=round(storage_gb, 8),
                writes_per_user_per_month=writes,
                reads_per_user_per_month=reads,
                average_object_size_kb=avg_kb,
                reasoning=reasoning.strip(),
            )
        )
        writes_per_user += writes
        reads_per_user += reads
        if reads > 0:
            weighted_download_kb += reads * avg_kb
            read_weight += reads

    avg_download = weighted_download_kb / read_weight if read_weight else 64.0
    return S3StorageDerivation(
        static_storage_gb=round(static_total, 4),
        storage_gb_per_user=round(max(per_user_total, 0.0), 8),
        writes_per_user_per_month=writes_per_user,
        reads_per_user_per_month=reads_per_user,
        avg_download_size_kb=round(avg_download, 2),
        categories=tuple(categories),
    )


def rds_entity_assumptions(derivation: RdsStorageDerivation) -> list[UsageAssumption]:
    """Expose entity breakdown as UsageAssumption rows for reporting."""
    rows: list[UsageAssumption] = []
    for entity in derivation.entities:
        rows.append(
            UsageAssumption(
                key=f"storage_entity:{entity.entity}",
                value=round(entity.storage_gb_per_user, 6),
                unit="GB/user",
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.medium,
                reasoning=(
                    f"{entity.records_per_user_per_month} rec/user/mo × "
                    f"{entity.average_record_size_kb} KB × {entity.retention_months} mo retention "
                    f"→ {entity.storage_gb_per_user:.6f} GB/user. {entity.reasoning}"
                ),
            )
        )
    rows.append(
        UsageAssumption(
            key="backup_retention_days",
            value=derivation.backup_retention_days,
            unit="days",
            source=AssumptionSource.inferred,
            confidence=AssumptionConfidence.high,
            reasoning=(
                f"Backup storage derived from DB size × {derivation.backup_retention_days}/30 "
                f"retention window (not guessed independently)."
            ),
        )
    )
    return rows


def s3_category_assumptions(derivation: S3StorageDerivation) -> list[UsageAssumption]:
    rows: list[UsageAssumption] = []
    for category in derivation.categories:
        unit = "GB total" if category.scaling == "static" else "GB/user"
        rows.append(
            UsageAssumption(
                key=f"storage_category:{category.category}",
                value=round(category.storage_gb, 6),
                unit=unit,
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.medium,
                reasoning=category.reasoning,
            )
        )
    if derivation.static_storage_gb > 0:
        rows.append(
            UsageAssumption(
                key="static_storage_gb",
                value=derivation.static_storage_gb,
                unit="GB total",
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.high,
                reasoning="Sum of static (non-user-scaling) S3 categories.",
            )
        )
    return rows


def inject_rds_storage_into_behavioral(
    behavioral: dict[str, UsageAssumption],
    derivation: RdsStorageDerivation,
) -> list[UsageAssumption]:
    behavioral["storage_gb_per_user"] = UsageAssumption(
        key="storage_gb_per_user",
        value=derivation.storage_gb_per_user,
        unit="GB/user",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning=(
            "Sum of entity-level storage: "
            + ", ".join(
                f"{e.entity}={e.storage_gb_per_user:.6f} GB/user" for e in derivation.entities
            )
        ),
    )
    behavioral["backup_storage_gb_per_user"] = UsageAssumption(
        key="backup_storage_gb_per_user",
        value=derivation.backup_storage_gb_per_user,
        unit="GB/user/month",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning=(
            f"Derived from {derivation.storage_gb_per_user:.6f} GB/user database storage × "
            f"{derivation.backup_retention_days}-day backup retention policy."
        ),
    )
    return rds_entity_assumptions(derivation)


def inject_s3_storage_into_behavioral(
    behavioral: dict[str, UsageAssumption],
    config: dict[str, UsageAssumption],
    derivation: S3StorageDerivation,
) -> list[UsageAssumption]:
    behavioral["storage_gb_per_user"] = UsageAssumption(
        key="storage_gb_per_user",
        value=derivation.storage_gb_per_user,
        unit="GB/user",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning=(
            "Sum of per-user S3 categories: "
            + ", ".join(
                f"{c.category}={c.storage_gb:.6f} GB/user"
                for c in derivation.categories
                if c.scaling == "per_user"
            )
            or "no per-user categories"
        ),
    )
    behavioral["writes_per_user_per_month"] = UsageAssumption(
        key="writes_per_user_per_month",
        value=derivation.writes_per_user_per_month,
        unit="operations/user/month",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.medium,
        reasoning="Summed writes across S3 storage categories.",
    )
    behavioral["reads_per_user_per_month"] = UsageAssumption(
        key="reads_per_user_per_month",
        value=derivation.reads_per_user_per_month,
        unit="operations/user/month",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.medium,
        reasoning="Summed reads across S3 storage categories.",
    )
    behavioral["avg_download_size_kb"] = UsageAssumption(
        key="avg_download_size_kb",
        value=derivation.avg_download_size_kb,
        unit="KB/read",
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.medium,
        reasoning="Read-weighted average object size across S3 categories.",
    )
    if derivation.static_storage_gb > 0:
        config["static_storage_gb"] = UsageAssumption(
            key="static_storage_gb",
            value=derivation.static_storage_gb,
            unit="GB total",
            source=AssumptionSource.inferred,
            confidence=AssumptionConfidence.high,
            reasoning="Static assets and shared content — does not scale with user count.",
        )
    return s3_category_assumptions(derivation)
