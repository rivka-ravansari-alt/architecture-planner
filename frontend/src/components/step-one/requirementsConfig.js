/**
 * Business-level requirement cards for Step 1.
 *
 * Only information a product owner is expected to know is collected here.
 * No infrastructure details (CPU, memory, database engine, cache, queues,
 * cloud providers, networking, etc.) - those are decided by the system later.
 *
 * Field types:
 *  - checkbox_group: multi-select list of options -> string[]
 *  - number:         validated non-negative number (integer when `integer`)
 *  - textarea:       free text -> string
 */
export const REQUIREMENT_CARDS = [
  {
    id: "authentication",
    title: "Authentication",
    question: "Does your application require user authentication?",
    fields: [],
  },
  {
    id: "file_uploads",
    title: "File Uploads",
    question: "Will users upload files?",
    fields: [
      {
        key: "files_per_month",
        type: "radio",
        label: "How many files are uploaded each month?",
        options: [
          { value: "<100", label: "Less than 100" },
          { value: "100-1000", label: "100 – 1,000" },
          { value: "1000-10000", label: "1,000 – 10,000" },
          { value: "10000-100000", label: "10,000 – 100,000" },
          { value: ">100000", label: "More than 100,000" },
        ],
      },
      {
        key: "average_file_size",
        type: "radio",
        label: "Average file size",
        options: [
          { value: "<1mb", label: "Small (< 1 MB)" },
          { value: "1-10mb", label: "Medium (1–10 MB)" },
          { value: "10-100mb", label: "Large (10–100 MB)" },
          { value: ">100mb", label: "Very Large (> 100 MB)" },
        ],
      },
    ],
  },
  {
    id: "background_processing",
    title: "Background Processing",
    question: "Does your application perform background processing?",
    fields: [],
  },
  {
    id: "dashboards_reports",
    title: "Dashboards & Reports",
    question: "Does the application include dashboards or reports?",
    fields: [
      {
        key: "features",
        type: "checkbox_group",
        label: "Included features",
        options: [
          { value: "dashboard", label: "Dashboard" },
          { value: "reports", label: "Reports" },
          { value: "export_pdf", label: "Export to PDF" },
          { value: "export_excel", label: "Export to Excel" },
          { value: "export_csv", label: "Export to CSV" },
        ],
      },
    ],
  },
  {
    id: "ai_usage",
    title: "AI Usage",
    question: "Does your application use AI?",
    fields: [
      {
        key: "ai_type",
        type: "radio",
        label: "AI type",
        options: [
          { value: "ai_chat", label: "AI Chat" },
          { value: "content_generation", label: "Content Generation" },
          { value: "document_processing", label: "Document Processing" },
          { value: "image_processing", label: "Image Processing" },
          { value: "other", label: "Other" },
        ],
      },
      {
        key: "usage_frequency",
        type: "radio",
        label: "How often will users use AI?",
        options: [
          { value: "low", label: "Low (1–10 requests per user per month)" },
          { value: "medium", label: "Medium (10–100 requests per user per month)" },
          { value: "high", label: "High (100–1,000 requests per user per month)" },
          { value: "very_high", label: "Very High (1,000+ requests per user per month)" },
        ],
      },
    ],
  },
  {
    id: "payments",
    title: "Payments",
    question: "Does your application process payments?",
    fields: [],
  },
  {
    id: "notifications",
    title: "Notifications",
    question: "Does your application send notifications?",
    fields: [
      {
        key: "channels",
        type: "checkbox_group",
        label: "Notification channels",
        options: [
          { value: "email", label: "Email" },
          { value: "push", label: "Push" },
          { value: "sms", label: "SMS" },
          { value: "in_app", label: "In-app" },
        ],
      },
    ],
  },
  {
    id: "external_integrations",
    title: "External Integrations",
    question: "Does your application integrate with external systems?",
    fields: [
      {
        key: "description",
        type: "textarea",
        label: "Briefly describe the integrations",
        placeholder: "Stripe, Google Maps, Slack, GitHub",
      },
    ],
  },
  {
    id: "realtime",
    title: "Real-time Features",
    question: "Does your application require real-time communication?",
    fields: [
      {
        key: "features",
        type: "checkbox_group",
        label: "Real-time features",
        options: [
          { value: "chat", label: "Chat" },
          { value: "live_notifications", label: "Live notifications" },
          { value: "live_dashboard_updates", label: "Live dashboard updates" },
          { value: "live_tracking", label: "Live tracking" },
          { value: "other", label: "Other" },
        ],
      },
    ],
  },
  {
    id: "reliability",
    title: "Reliability",
    question: "Does your application have special reliability requirements?",
    fields: [
      {
        key: "options",
        type: "checkbox_group",
        label: "Reliability needs",
        options: [
          { value: "high_availability", label: "High availability required" },
          { value: "automatic_backups", label: "Automatic backups" },
          { value: "handle_traffic_spikes", label: "Handle traffic spikes" },
        ],
      },
      {
        key: "description",
        type: "textarea",
        label: "Short description (optional)",
      },
    ],
  },
];

function defaultFieldValue(field) {
  return field.type === "checkbox_group" ? [] : "";
}

/** Build the initial (all-disabled) requirements state. */
export function buildInitialRequirements() {
  const state = {};
  for (const card of REQUIREMENT_CARDS) {
    const entry = { enabled: false };
    for (const field of card.fields) {
      entry[field.key] = defaultFieldValue(field);
    }
    state[card.id] = entry;
  }
  return state;
}

/**
 * Validate numeric fields of enabled requirements.
 * Numbers are optional; only non-empty invalid values produce errors.
 * @returns {Record<string, string>} keyed by `${cardId}.${fieldKey}`
 */
export function validateRequirements(requirements) {
  const errors = {};
  for (const card of REQUIREMENT_CARDS) {
    const entry = requirements?.[card.id];
    if (!entry?.enabled) continue;

    for (const field of card.fields) {
      if (field.type !== "number") continue;
      const raw = entry[field.key];
      if (raw === "" || raw === null || raw === undefined) continue;

      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0) {
        errors[`${card.id}.${field.key}`] = "Enter a valid non-negative number.";
      } else if (field.integer && !Number.isInteger(value)) {
        errors[`${card.id}.${field.key}`] = "Enter a whole number.";
      }
    }
  }
  return errors;
}

/**
 * Produce clean, structured JSON for submission.
 * Disabled requirements collapse to `{ enabled: false }`; numbers are coerced
 * and empty text is omitted.
 */
export function serializeRequirements(requirements) {
  const output = {};
  for (const card of REQUIREMENT_CARDS) {
    const entry = requirements?.[card.id] ?? { enabled: false };
    if (!entry.enabled) {
      output[card.id] = { enabled: false };
      continue;
    }

    const serialized = { enabled: true };
    for (const field of card.fields) {
      const value = entry[field.key];
      if (field.type === "number") {
        if (value === "" || value === null || value === undefined) continue;
        serialized[field.key] = Number(value);
      } else if (field.type === "checkbox_group") {
        serialized[field.key] = Array.isArray(value) ? value : [];
      } else if (typeof value === "string" && value.trim()) {
        serialized[field.key] = value.trim();
      }
    }
    output[card.id] = serialized;
  }
  return output;
}
