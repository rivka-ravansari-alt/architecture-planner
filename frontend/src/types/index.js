/** @typedef {{ id: string; label: string; description?: string }} ProjectTypeOption */
/** @typedef {{ id: string; label: string }} SelectOption */

/** @typedef {Object} IntakeProduct
 * @property {string} name
 * @property {string} description
 * @property {string[]} platforms
 * @property {string} expected_users
 */

/** @typedef {Object} IntakeFeatureState
 * @property {boolean} enabled
 */

/** @typedef {Object} IntakeForm
 * @property {IntakeProduct} product
 * @property {Record<string, IntakeFeatureState & Record<string, unknown>>} features
 */

/** @typedef {Object} RequirementAnswers
 * @property {boolean} auth
 * @property {boolean} file_upload
 * @property {boolean} background_processing
 * @property {boolean} dashboards
 * @property {boolean} ai
 * @property {boolean} payments
 * @property {boolean} include_edge_cases
 */

/** @typedef {Object} CloudMapping
 * @property {string[]} aws
 * @property {string[]} gcp
 * @property {string[]} azure
 */

/** @typedef {Object} ArchitectureComponent
 * @property {string} key
 * @property {string} name
 * @property {string} type
 * @property {string} reason
 * @property {boolean} optional
 * @property {Object} [implementation_options]
 *   Recommended key plus per-model detail objects (when_to_use, cost_impact, pros, cons).
 * @property {CloudMapping} [cloud_mapping]
 */

/** @typedef {Object} Project
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {string[]} project_types
 * @property {string} stage
 * @property {string} expected_users
 * @property {string} [generated_at]
 * @property {string} [architecture_summary]
 * @property {string[]} [main_flow]
 * @property {Object} [architecture_diagrams]
 * @property {CostBreakdown} [cost_breakdown]
 */

/** @typedef {Object} User
 * @property {string} id
 * @property {string} email
 * @property {string} name
 * @property {string} [picture]
 */

/** @typedef {Object} CostRange
 * @property {number} low
 * @property {number} high
 */

/** @typedef {"low" | "medium" | "high"} CostConfidence */

/** @typedef {Object} ProviderCostMatrix
 * @property {CostRange} aws
 * @property {CostRange} gcp
 * @property {CostRange} azure
 */

/** @typedef {Object} CloudInfrastructureCost
 * @property {Record<string, ProviderCostMatrix>} categories
 * @property {Record<string, CostRange>} provider_totals
 */

/** @typedef {Object} CostBreakdown
 * @property {CloudInfrastructureCost} [cloud_infrastructure]
 * @property {Record<string, CostRange>} cloud_cost
 * @property {Record<string, CostRange>} [ai_services_cost]
 * @property {Record<string, CostRange>} external_services_cost
 * @property {CostRange} total_monthly_cost
 * @property {string[]} [assumptions]
 * @property {string[]} [unknown_items]
 * @property {CostConfidence} [confidence]
 * @property {string} [disclaimer]
 * @property {string} [currency]
 */

export {};
