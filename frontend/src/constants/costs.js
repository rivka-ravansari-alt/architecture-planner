export const COST_PROVIDERS = ["aws", "gcp", "azure"];

export const COST_CURRENCY = "USD";

/** Must match backend CALCULATOR_VERSION_PROFILE_DRIVEN. */
export const CALCULATOR_VERSION_PROFILE_DRIVEN = "profile_driven_v1";

export function isCurrentPricingEstimate(estimate) {
  return estimate?.calculator_version === CALCULATOR_VERSION_PROFILE_DRIVEN;
}

export function isPricedBreakdownRow(row) {
  return Boolean(row?.pricing_profile_id);
}
