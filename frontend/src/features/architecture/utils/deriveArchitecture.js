/** @typedef {{ low: number; high: number }} CostRange */

/**
 * @typedef {Object} CostBreakdown
 * @property {Record<string, CostRange>} cloud_cost
 * @property {Record<string, CostRange>} external_services_cost
 * @property {CostRange} total_monthly_cost
 * @property {string} [currency]
 */

/**
 * @param {import("../../../types/index.js").Project | null} project
 * @returns {{ costs: CostBreakdown | null }}
 */
export function deriveArchitecture(project) {
  return {
    costs: project?.cost_breakdown ?? null,
  };
}
