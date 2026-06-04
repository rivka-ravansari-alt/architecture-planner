/** @typedef {{ id: string; label: string; description?: string }} ProjectTypeOption */
/** @typedef {{ id: string; label: string }} SelectOption */

/** @typedef {Object} WizardForm
 * @property {string} name
 * @property {string} description
 * @property {string[]} project_types
 * @property {string} stage
 * @property {string} expected_users
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
 * @property {string[]} [next_steps]
 * @property {Array<{title: string; description: string; severity: string}>} [risks]
 * @property {Array<{text: string}>} [recommendations]
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
