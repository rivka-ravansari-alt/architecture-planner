import {
  CALCULATOR_VERSION_PROFILE_DRIVEN,
  COST_CURRENCY,
  isPricedBreakdownRow,
} from "../../../constants/costs.js";

function mapBackendCostEstimate(estimate) {
  const requiredLow = Math.round(estimate.required_monthly_low ?? 0);
  const requiredHigh = Math.round(estimate.required_monthly_high ?? 0);
  const optionalLow = Math.round(estimate.optional_monthly_low ?? 0);
  const optionalHigh = Math.round(estimate.optional_monthly_high ?? 0);

  const debugTable =
    estimate.pricing_debug_table?.length > 0
      ? estimate.pricing_debug_table
      : (estimate.component_breakdown ?? []);

  return {
    provider: estimate.provider,
    calculatorVersion: estimate.calculator_version ?? null,
    requiredLow,
    requiredHigh,
    optionalLow,
    optionalHigh,
    totalLow: requiredLow,
    totalHigh: requiredHigh,
    currency: estimate.currency || COST_CURRENCY,
    unknownItems: estimate.unknown_items ?? [],
    warnings: estimate.warnings ?? [],
    notes: estimate.notes ?? "",
    componentBreakdown: debugTable,
    pricingDebugTable: debugTable.map((row) => ({
      ...row,
      isPriced: isPricedBreakdownRow(row),
    })),
  };
}

export function deriveArchitecture(project) {
  const estimates = project?.cost_estimates ?? [];
  return {
    costs: estimates.map(mapBackendCostEstimate),
    expectedCalculatorVersion: CALCULATOR_VERSION_PROFILE_DRIVEN,
  };
}

export { isPricedBreakdownRow };
