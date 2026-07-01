import { STAGES } from "../constants/wizard.js";

/** @typedef {'text' | 'textarea' | 'select' | 'multi_select' | 'checkbox_group' | 'radio' | 'boolean' | 'number'} FieldType */

/** @typedef {{ value: string; label: string; disabled?: boolean }} FieldOption */

/**
 * @typedef {Object} FormField
 * @property {string} key
 * @property {FieldType} type
 * @property {string} [label]
 * @property {string} [placeholder]
 * @property {FieldOption[]} [options]
 * @property {boolean} [required]
 * @property {string} [defaultValue]
 * @property {{ field: string; value: string }} [showWhen]
 * @property {boolean} [requiresChannels]
 */

/**
 * @typedef {Object} UsageToggleGroup
 * @property {string} key
 * @property {string} title
 * @property {string} label
 * @property {string} [description]
 * @property {string[]} [examples]
 * @property {FormField[]} fields
 */

/**
 * @typedef {Object} UsageQuestionBlock
 * @property {string} key
 * @property {string} title
 * @property {string} [description]
 * @property {string[]} [examples]
 * @property {FormField[]} fields
 */

export const PLATFORM_OPTIONS = [
  { value: "web", label: "Web" },
  { value: "mobile", label: "Mobile" },
  { value: "both", label: "Both" },
];

export const STAGE_OPTIONS = STAGES.map(({ id, label }) => ({
  value: id,
  label,
  ...(id === "production" ? { disabled: true } : {}),
}));

export const MONTHLY_ACTIVE_USERS_OPTIONS = [
  { value: "100", label: "100" },
  { value: "1000", label: "1,000" },
  { value: "10000", label: "10,000" },
  { value: "100000+", label: "100,000+" },
  { value: "custom", label: "Custom" },
];

export const USER_ACTIVITY_OPTIONS = [
  { value: "light", label: "Light (1–5 actions per day)" },
  { value: "moderate", label: "Moderate (5–20 actions per day)" },
  { value: "heavy", label: "Heavy (20–100 actions per day)" },
  { value: "very_heavy", label: "Very Heavy (100+ actions per day)" },
];

export const FILES_PER_MONTH_OPTIONS = [
  { value: "under_1k", label: "Less than 1,000" },
  { value: "1k_10k", label: "1,000–10,000" },
  { value: "10k_100k", label: "10,000–100,000" },
  { value: "100k_plus", label: "More than 100,000" },
];

export const FILE_SIZE_OPTIONS = [
  { value: "small", label: "Small (<1 MB)" },
  { value: "medium", label: "Medium (1–10 MB)" },
  { value: "large", label: "Large (>10 MB)" },
];

export const AI_REQUESTS_PER_USER_OPTIONS = [
  { value: "under_1", label: "Less than 1" },
  { value: "1_5", label: "1–5" },
  { value: "5_20", label: "5–20" },
  { value: "20_plus", label: "More than 20" },
];

export const AI_SIZE_OPTIONS = [
  { value: "small", label: "Small" },
  { value: "medium", label: "Medium" },
  { value: "large", label: "Large" },
];

export const BACKGROUND_JOBS_OPTIONS = [
  { value: "none", label: "None" },
  { value: "low", label: "Low" },
  { value: "moderate", label: "Moderate" },
  { value: "heavy", label: "Heavy" },
];

export const NOTIFICATION_CHANNEL_OPTIONS = [
  { value: "email", label: "Email" },
  { value: "sms", label: "SMS" },
  { value: "push", label: "Push Notifications" },
];

export const NOTIFICATION_VOLUME_OPTIONS = [
  { value: "under_1k", label: "Less than 1,000" },
  { value: "1k_10k", label: "1,000–10,000" },
  { value: "10k_100k", label: "10,000–100,000" },
  { value: "100k_plus", label: "More than 100,000" },
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
];

/** @type {UsageQuestionBlock[]} */
export const USAGE_QUESTION_BLOCKS = [
  {
    key: "monthly_active_users",
    title: "Expected Monthly Active Users",
    description: "How many active users do you expect each month?",
    fields: [
      {
        key: "monthly_active_users",
        type: "select",
        options: MONTHLY_ACTIVE_USERS_OPTIONS,
        required: true,
        defaultValue: "100",
      },
      {
        key: "custom_monthly_active_users",
        type: "number",
        label: "Custom monthly active users",
        placeholder: "e.g. 2500",
        showWhen: { field: "monthly_active_users", value: "custom" },
      },
    ],
  },
  {
    key: "user_activity",
    title: "Average User Activity",
    description:
      "How often does a typical active user interact with your application? Actions include page views, form submissions, API calls, and similar interactions.",
    examples: [
      "Opening the dashboard once per day",
      "Submitting several forms throughout the day",
      "Frequent real-time updates or searches",
    ],
    fields: [
      {
        key: "user_activity",
        type: "radio",
        options: USER_ACTIVITY_OPTIONS,
        required: true,
        defaultValue: "moderate",
      },
    ],
  },
  {
    key: "background_jobs",
    title: "Background Tasks",
    description: "Does your application perform work after the user action completes?",
    examples: [
      "AI processing",
      "File processing",
      "Scheduled jobs",
      "Report generation",
      "Data synchronization",
      "Sending emails asynchronously",
    ],
    fields: [
      {
        key: "background_jobs",
        type: "radio",
        options: BACKGROUND_JOBS_OPTIONS,
        required: true,
        defaultValue: "none",
      },
    ],
  },
];

/** @type {UsageToggleGroup[]} */
export const USAGE_TOGGLE_GROUPS = [
  {
    key: "file_uploads",
    title: "File Uploads",
    description:
      "Enable if users can upload documents, images, videos, or other files. Upload volume and file size affect storage and bandwidth estimates.",
    examples: [
      "Profile photos",
      "PDF or document uploads",
      "Video or media attachments",
    ],
    label: "Does your application allow users to upload files?",
    fields: [
      {
        key: "files_per_month",
        type: "radio",
        label: "Files uploaded per month",
        options: FILES_PER_MONTH_OPTIONS,
        defaultValue: "under_1k",
      },
      {
        key: "average_file_size",
        type: "radio",
        label: "Average file size",
        options: FILE_SIZE_OPTIONS,
        defaultValue: "small",
      },
    ],
  },
  {
    key: "ai",
    title: "Artificial Intelligence",
    description:
      "Enable if your application calls AI models for inference, generation, embeddings, or similar workloads.",
    examples: [
      "Chat assistants",
      "Document summarization",
      "Image or audio analysis",
      "Semantic search and recommendations",
    ],
    label: "Does your application use AI?",
    fields: [
      {
        key: "requests_per_user_per_day",
        type: "radio",
        label: "Average AI requests per active user per day",
        options: AI_REQUESTS_PER_USER_OPTIONS,
        defaultValue: "under_1",
      },
      {
        key: "prompt_size",
        type: "radio",
        label: "Average prompt size",
        options: AI_SIZE_OPTIONS,
        defaultValue: "small",
      },
      {
        key: "response_size",
        type: "radio",
        label: "Average response size",
        options: AI_SIZE_OPTIONS,
        defaultValue: "medium",
      },
    ],
  },
  {
    key: "notifications",
    title: "Notifications",
    description: "Enable if your application sends outbound notifications to users.",
    examples: [
      "Account alerts via email",
      "OTP codes via SMS",
      "Mobile push notifications",
    ],
    label: "Does your application send notifications?",
    fields: [
      {
        key: "channels",
        type: "checkbox_group",
        label: "Channels",
        options: NOTIFICATION_CHANNEL_OPTIONS,
      },
      {
        key: "volume_per_month",
        type: "radio",
        label: "Estimated notifications per month",
        options: NOTIFICATION_VOLUME_OPTIONS,
        defaultValue: "under_1k",
        requiresChannels: true,
      },
    ],
  },
];

/** Required product field keys for step-1 validation. */
export const INTAKE_VALIDATION = {
  product: ["name", "description", "platforms", "stage"],
  usage: ["monthly_active_users", "user_activity", "background_jobs"],
};

/**
 * Maps usage answers to legacy backend requirement booleans for AI component generation.
 * @type {Record<string, (usage: Record<string, unknown>) => boolean>}
 */
export const LEGACY_ANSWER_MAPPING = {
  auth: () => true,
  file_upload: (usage) => Boolean(usage.file_uploads?.enabled),
  background_processing: (usage) => usage.background_jobs !== "none",
  dashboards: (usage) =>
    usage.user_activity === "heavy" || usage.user_activity === "very_heavy",
  ai: (usage) => Boolean(usage.ai?.enabled),
  payments: () => false,
  include_edge_cases: (usage) =>
    usage.monthly_active_users === "100000+" ||
    usage.user_activity === "very_heavy" ||
    usage.background_jobs === "heavy",
};

/** Single configuration object for sections, usage questions, validation, and API mapping. */
export const INTAKE_FORM_CONFIG = {
  productSection: {
    id: "product",
    title: "Product",
    subtitle: "Basic details that shape platform choice and scale.",
    fields: BASIC_PRODUCT_FIELDS,
    validation: INTAKE_VALIDATION.product,
  },
  usageSection: {
    id: "usage",
    title: "Usage Profile",
    subtitle:
      "Answer a few questions about how your application will be used. We'll estimate cloud resource consumption from your answers.",
    questionBlocks: USAGE_QUESTION_BLOCKS,
    toggleGroups: USAGE_TOGGLE_GROUPS,
    validation: INTAKE_VALIDATION.usage,
  },
  legacyAnswerMapping: LEGACY_ANSWER_MAPPING,
};
