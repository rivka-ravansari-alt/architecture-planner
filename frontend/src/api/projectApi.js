import { apiRequest } from "./client.js";

/**
 * @typedef {Object} SelectedComponent
 * @property {string} instance_id unique per-instance id (same category may repeat)
 * @property {string} category_id Firestore architecture category id (mapping/pricing)
 * @property {string} name
 * @property {string} description
 * @property {string|null} [type]
 * @property {string} reason
 * @property {"ai_selected"|"user_added"} [source]
 * @property {string|null} [explanation]
 */

/**
 * @typedef {Object} ComponentSelection
 * @property {string} selection_id Firestore document id for this selection
 * @property {SelectedComponent[]} selected
 * @property {SelectedComponent[]} excluded
 */

/**
 * @typedef {Object} ArchitectureCategory
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {string|null} [type]
 */

const GENERATE_TIMEOUT_MS = 300_000;

export const projectApi = {
  /**
   * Create a project (Step 1 intake).
   * @param {{ description: string, platform: "web"|"mobile", stage: "mvp"|"production", expected_users: number, requirements: object }} payload
   * @returns {Promise<{ id: string }>}
   */
  createProject: (payload) =>
    apiRequest("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /**
   * Generate the architecture component selection (Step 2).
   * @param {string} projectId
   * @returns {Promise<ComponentSelection>}
   */
  generateArchitectureComponents: (projectId) =>
    apiRequest(`/projects/${projectId}/architecture-components/generate`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),

  /**
   * Load the latest saved component selection (without re-generating).
   * @param {string} projectId
   * @returns {Promise<ComponentSelection>}
   */
  getArchitectureSelection: (projectId) =>
    apiRequest(`/projects/${projectId}/architecture-components/selection`),

  /**
   * List all architecture categories from Firestore (for the add modal).
   * @returns {Promise<ArchitectureCategory[]>}
   */
  listArchitectureCategories: () => apiRequest("/architecture-categories"),

  /**
   * Manually add a component from an architecture category.
   * @param {string} projectId
   * @param {{ selection_id: string, category_id: string, explanation?: string|null }} payload
   * @returns {Promise<ComponentSelection>}
   */
  addArchitectureComponent: (projectId, payload) =>
    apiRequest(`/projects/${projectId}/architecture-components`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /**
   * Remove a selected component instance (moves it to the excluded list).
   * @param {string} projectId
   * @param {string} selectionId Firestore selection document id
   * @param {string} instanceId unique per-instance id
   * @returns {Promise<ComponentSelection>}
   */
  removeArchitectureComponent: (projectId, selectionId, instanceId) =>
    apiRequest(
      `/projects/${projectId}/architecture-components/${encodeURIComponent(instanceId)}?selection_id=${encodeURIComponent(selectionId)}`,
      { method: "DELETE" }
    ),

  /**
   * Generate the global usage model (Step 3).
   * @param {string} projectId
   * @returns {Promise<object>}
   */
  generateGlobalUsageModel: (projectId) =>
    apiRequest(`/projects/${projectId}/usage-model/generate`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),

  /**
   * Load the latest global usage model.
   * @param {string} projectId
   * @returns {Promise<object>}
   */
  getGlobalUsageModel: (projectId) =>
    apiRequest(`/projects/${projectId}/usage-model`),

  /**
   * Generate pricing for a single cloud provider (Step 4).
   * @param {string} projectId
   * @param {"aws"|"azure"|"gcp"} provider
   * @param {string|null} [runId]
   * @returns {Promise<ProviderPricingResponse>}
   */
  generateProviderPricing: (projectId, provider, runId = null) => {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
    return apiRequest(`/projects/${projectId}/pricing/generate/${provider}${query}`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    });
  },

  /**
   * Load the latest pricing run with all provider results.
   * @param {string} projectId
   * @returns {Promise<PricingRun>}
   */
  getLatestPricing: (projectId) => apiRequest(`/projects/${projectId}/pricing`),

  /**
   * Load a specific pricing run.
   * @param {string} projectId
   * @param {string} runId
   * @returns {Promise<PricingRun>}
   */
  getPricingRun: (projectId, runId) =>
    apiRequest(`/projects/${projectId}/pricing/runs/${encodeURIComponent(runId)}`),
};

/**
 * @typedef {Object} PricingLineItem
 * @property {string} instance_id
 * @property {string} category_id
 * @property {string} component_name
 * @property {string|null} [service_id]
 * @property {string|null} [service_name]
 * @property {string|null} [service_type]
 * @property {number|null} [monthly_price]
 * @property {"priced"|"skipped"|"failed"} [status]
 * @property {string|null} [skip_reason]
 * @property {string|null} [selection_reason]
 * @property {string[]} [calculation_summary]
 */

/**
 * @typedef {Object} ProviderPricingResult
 * @property {string} provider
 * @property {string} provider_label
 * @property {"pending"|"calculating"|"completed"|"failed"} status
 * @property {PricingLineItem[]} line_items
 * @property {number} monthly_total
 * @property {string|null} [error]
 */

/**
 * @typedef {Object} ProviderPricingResponse
 * @property {string} run_id
 * @property {string} selection_id
 * @property {string} usage_model_id
 * @property {ProviderPricingResult} result
 */

/**
 * @typedef {Object} PricingComparisonRow
 * @property {string} provider
 * @property {string} provider_label
 * @property {number|null} monthly_total
 * @property {"pending"|"calculating"|"completed"|"failed"} status
 */

/**
 * @typedef {Object} PricingRun
 * @property {string} run_id
 * @property {string} selection_id
 * @property {string} usage_model_id
 * @property {ProviderPricingResult[]} providers
 * @property {PricingComparisonRow[]} comparison
 */
