/** @typedef {'text' | 'textarea' | 'select' | 'multi_select' | 'checkbox_group' | 'radio' | 'boolean'} FieldType */

/** @typedef {{ value: string; label: string; disabled?: boolean }} FieldOption */

/**
 * @typedef {Object} FormField
 * @property {string} key
 * @property {FieldType} type
 * @property {string} label
 * @property {string} [placeholder]
 * @property {FieldOption[]} [options]
 * @property {boolean} [required]
 * @property {string} [defaultValue]
 */

/**
 * @typedef {Object} FeatureToggle
 * @property {string} key
 * @property {string} label
 * @property {FormField[]} fields
 */

export const PLATFORM_OPTIONS = [
  { value: "web", label: "Web" },
  { value: "mobile", label: "Mobile" },
  { value: "both", label: "Both" },
];

export const EXPECTED_USERS_OPTIONS = [
  { value: "100", label: "Up to 100" },
  { value: "1000", label: "Up to 1,000" },
  { value: "10000", label: "Up to 10,000" },
  { value: "100000+", label: "100,000+" },
];

export const STAGE_OPTIONS = [
  { value: "mvp", label: "MVP" },
  { value: "production", label: "Production", disabled: true },
];

/** @type {FormField[]} */
export const BASIC_PRODUCT_FIELDS = [
  {
    key: "name",
    type: "text",
    label: "Product name",
    placeholder: "e.g. Task Manager",
    required: true,
  },
  {
    key: "description",
    type: "textarea",
    label: "Product description",
    placeholder: "A short description of what the app does...",
    required: true,
  },
  {
    key: "platforms",
    type: "multi_select",
    label: "Platform",
    options: PLATFORM_OPTIONS,
    required: true,
  },
  {
    key: "stage",
    type: "select",
    label: "Stage",
    options: STAGE_OPTIONS,
    required: true,
    defaultValue: "mvp",
  },
  {
    key: "expected_users",
    type: "select",
    label: "Expected users",
    options: EXPECTED_USERS_OPTIONS,
    required: true,
    defaultValue: "100",
  },
];

/**
 * Architecture capability toggles — only questions that affect components,
 * cloud services, scaling, and monthly cost estimates.
 * @type {FeatureToggle[]}
 */
export const FEATURE_TOGGLES = [
  {
    key: "authentication",
    label: "Does the system require user accounts?",
    fields: [
      {
        key: "enterprise_sso",
        type: "boolean",
        label: "Enterprise SSO?",
      },
    ],
  },
  {
    key: "file_uploads",
    label: "Does the system upload files?",
    fields: [
      {
        key: "estimated_files_per_month",
        type: "radio",
        label: "Estimated files per month",
        options: [
          { value: "under_1k", label: "<1K" },
          { value: "1k_10k", label: "1K–10K" },
          { value: "10k_plus", label: "10K+" },
        ],
      },
      {
        key: "average_file_size",
        type: "radio",
        label: "Average file size",
        options: [
          { value: "small", label: "Small" },
          { value: "medium", label: "Medium" },
          { value: "large", label: "Large" },
        ],
      },
      {
        key: "process_after_upload",
        type: "boolean",
        label: "Are files processed after upload?",
      },
    ],
  },
  {
    key: "ai",
    label: "Does the system use AI?",
    fields: [
      {
        key: "ai_types",
        type: "checkbox_group",
        label: "AI type",
        options: [
          { value: "chat", label: "Chat" },
          { value: "document_processing", label: "Document Processing" },
          { value: "recommendations", label: "Recommendations" },
          { value: "search", label: "Search" },
          { value: "image_generation", label: "Image Generation" },
          { value: "audio_processing", label: "Audio Processing" },
        ],
      },
      {
        key: "estimated_ai_requests_per_day",
        type: "radio",
        label: "Estimated AI requests per day",
        options: [
          { value: "under_100", label: "<100" },
          { value: "100_1k", label: "100–1K" },
          { value: "1k_10k", label: "1K–10K" },
          { value: "10k_plus", label: "10K+" },
        ],
      },
    ],
  },
  {
    key: "dashboards",
    label: "Does the system require dashboards or reports?",
    fields: [],
  },
  {
    key: "payments",
    label: "Does the system require payments?",
    fields: [],
  },
  {
    key: "notifications",
    label: "Does the system send notifications?",
    fields: [],
  },
  {
    key: "external_integrations",
    label: "Does the system connect to external systems?",
    fields: [],
  },
  {
    key: "real_time",
    label: "Does the system require real-time updates?",
    fields: [
      {
        key: "real_time_types",
        type: "checkbox_group",
        label: "Real-time type",
        options: [
          { value: "live_chat", label: "Live Chat" },
          { value: "live_dashboard", label: "Live Dashboard" },
          { value: "collaboration", label: "Collaboration" },
        ],
      },
    ],
  },
  {
    key: "sensitive_data",
    label: "Does the system store sensitive data?",
    fields: [
      {
        key: "data_types",
        type: "checkbox_group",
        label: "Data type",
        options: [
          { value: "financial", label: "Financial" },
          { value: "medical", label: "Medical" },
          { value: "personal", label: "Personal" },
        ],
      },
    ],
  },
];

/** Required product field keys for step-1 validation. */
export const INTAKE_VALIDATION = {
  product: ["name", "description", "platforms", "stage", "expected_users"],
};

/**
 * Maps intake feature state to legacy backend requirement booleans.
 * @type {Record<string, (features: Record<string, Record<string, unknown>>) => boolean>}
 */
export const LEGACY_ANSWER_MAPPING = {
  auth: (features) => Boolean(features.authentication?.enabled),
  file_upload: (features) => Boolean(features.file_uploads?.enabled),
  background_processing: (features) =>
    Boolean(features.file_uploads?.enabled && features.file_uploads?.process_after_upload),
  dashboards: (features) => Boolean(features.dashboards?.enabled),
  ai: (features) => Boolean(features.ai?.enabled),
  payments: (features) => Boolean(features.payments?.enabled),
  include_edge_cases: (features) =>
    Boolean(
      features.sensitive_data?.enabled ||
        features.real_time?.enabled ||
        features.external_integrations?.enabled
    ),
};

/** Single configuration object for sections, toggles, validation, and API mapping. */
export const INTAKE_FORM_CONFIG = {
  productSection: {
    id: "product",
    title: "Product Information",
    subtitle: "Basic details that shape platform choice and scale.",
    fields: BASIC_PRODUCT_FIELDS,
    validation: INTAKE_VALIDATION.product,
  },
  architectureSection: {
    id: "architecture",
    title: "Architecture Capabilities",
    subtitle:
      "Enable only what affects infrastructure, cloud services, and monthly cost estimates.",
    toggles: FEATURE_TOGGLES,
  },
  legacyAnswerMapping: LEGACY_ANSWER_MAPPING,
};
