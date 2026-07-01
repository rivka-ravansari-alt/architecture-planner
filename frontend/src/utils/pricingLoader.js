import { api } from "../api/index.js";
import { WORKFLOW_STATUS } from "../constants/wizard.js";

function isNotFoundError(err) {
  const message = err?.message ?? "";
  return message === "Not Found" || message.includes("(404)");
}

/**
 * Load or refresh profile-driven pricing for a project.
 * Uses ensure-cost-estimates when available; falls back to approve + generate-pricing.
 */
export async function loadProjectPricing(project) {
  try {
    const refreshed = await api.ensureCostEstimates(project.id);
    if ((refreshed.cost_estimates?.length ?? 0) > 0) {
      return refreshed;
    }
  } catch (err) {
    if (!isNotFoundError(err)) {
      throw err;
    }
  }

  let current = project;
  if (
    current.workflow_status === WORKFLOW_STATUS.DIAGRAMS_GENERATED ||
    current.workflow_status === WORKFLOW_STATUS.PRICING_GENERATED
  ) {
    current = await api.approveArchitecture(project.id);
  }
  return api.generatePricing(current.id);
}
