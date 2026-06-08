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
 */

/** @typedef {Object} User
 * @property {string} id
 * @property {string} email
 * @property {string} name
 * @property {string} [picture]
 */

/** @typedef {Object} ProviderCost
 * @property {string} provider
 * @property {number} requiredLow
 * @property {number} requiredHigh
 * @property {number} optionalLow
 * @property {number} optionalHigh
 * @property {number} totalLow
 * @property {number} totalHigh
 * @property {string} currency
 */

export {};
