"""Azure Blob Storage SKU quantity formulas."""

from __future__ import annotations

from app.pricing.azure.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import (
    AzureServicePricingModel,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = ["storage_gb"]


def calculate_blob_storage_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(
            service=model.service,
            quantities=[],
            missing=missing,
            ready=False,
        )

    assumption_map = assumptions_by_key(resolved)
    storage_gb = numeric_value(assumption_map, "storage_gb")
    write_operations = optional_numeric(assumption_map, "write_operations", 0)
    read_operations = optional_numeric(assumption_map, "read_operations", 0)
    list_operations = optional_numeric(assumption_map, "list_operations", 0)
    data_retrieval_gb = optional_numeric(assumption_map, "data_retrieval_gb", 0)
    network_egress_gb = optional_numeric(assumption_map, "data_egress_gb", 0)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="storage_gb_month",
            quantity=float(storage_gb),
            unit="GB-months",
            formula="storage_gb",
            assumption_map=assumption_map,
            input_keys=["storage_gb"],
        ),
        make_quantity(
            sku_key="write_operations",
            quantity=float(write_operations),
            unit="operations/month",
            formula="write_operations",
            assumption_map=assumption_map,
            input_keys=["write_operations"],
        ),
        make_quantity(
            sku_key="read_operations",
            quantity=float(read_operations),
            unit="operations/month",
            formula="read_operations",
            assumption_map=assumption_map,
            input_keys=["read_operations"],
        ),
        make_quantity(
            sku_key="list_operations",
            quantity=float(list_operations),
            unit="operations/month",
            formula="list_operations",
            assumption_map=assumption_map,
            input_keys=["list_operations"] if "list_operations" in assumption_map else [],
            notes=(
                ["Defaults to 0 when list_operations is not provided."]
                if "list_operations" not in assumption_map
                else []
            ),
        ),
        make_quantity(
            sku_key="network_egress_gb",
            quantity=float(network_egress_gb),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]

    if data_retrieval_gb > 0:
        quantities.append(
            make_quantity(
                sku_key="retrieval_gb",
                quantity=float(data_retrieval_gb),
                unit="GB/month",
                formula="data_retrieval_gb",
                assumption_map=assumption_map,
                input_keys=["data_retrieval_gb", "access_tier"],
                notes=["Applies to Cool, Cold, and Archive tier data reads."],
            )
        )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
