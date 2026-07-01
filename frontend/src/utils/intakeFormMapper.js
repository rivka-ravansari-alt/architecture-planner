import { LEGACY_ANSWER_MAPPING } from "../config/intakeFormConfig.js";
import { buildIntakeOutput } from "./intakeFormState.js";

const PLATFORM_TO_PROJECT_TYPE = {
  web: "web_app",
  mobile: "mobile_app",
};

/**
 * Resolves the effective monthly active user count string for the API.
 * @param {Record<string, unknown>} usage
 */
export function resolveExpectedUsers(usage) {
  const tier = String(usage.monthly_active_users || "100");
  if (tier !== "custom") {
    return tier;
  }
  const custom = Number(usage.custom_monthly_active_users);
  if (Number.isFinite(custom) && custom > 0) {
    return String(Math.round(custom));
  }
  return "100";
}

/**
 * Builds the usage profile payload sent to the backend Usage Estimator.
 * @param {Record<string, unknown>} usage
 */
export function buildUsageProfile(usage) {
  const notifications = usage.notifications || {};
  const fileUploads = usage.file_uploads || {};
  const ai = usage.ai || {};
  const notificationsEnabled = Boolean(notifications.enabled);
  const channels = notificationsEnabled && Array.isArray(notifications.channels)
    ? notifications.channels
    : [];

  return {
    monthly_active_users: usage.monthly_active_users || "100",
    custom_monthly_active_users:
      usage.monthly_active_users === "custom"
        ? Number(usage.custom_monthly_active_users) || null
        : null,
    user_activity: usage.user_activity || "moderate",
    file_uploads_enabled: Boolean(fileUploads.enabled),
    files_per_month: fileUploads.files_per_month || "under_1k",
    average_file_size: fileUploads.average_file_size || "small",
    ai_enabled: Boolean(ai.enabled),
    ai_requests_per_user_per_day: ai.requests_per_user_per_day || "under_1",
    prompt_size: ai.prompt_size || "small",
    response_size: ai.response_size || "medium",
    background_jobs: usage.background_jobs || "none",
    notification_channels: channels,
    notifications_per_month: notifications.volume_per_month || "under_1k",
  };
}

/**
 * Maps the intake form JSON to the legacy API payload expected by the backend.
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function toLegacyPayload(intakeForm) {
  const output = buildIntakeOutput(intakeForm);
  const { product, usage } = output;

  /** @type {string[]} */
  const projectTypes = [];
  for (const platform of product.platforms) {
    const mapped = PLATFORM_TO_PROJECT_TYPE[platform];
    if (mapped && !projectTypes.includes(mapped)) {
      projectTypes.push(mapped);
    }
  }

  if (projectTypes.length === 0 && product.platforms.includes("both")) {
    projectTypes.push("web_app", "mobile_app");
  }

  /** @type {Record<string, boolean>} */
  const answers = {};
  for (const [key, resolver] of Object.entries(LEGACY_ANSWER_MAPPING)) {
    answers[key] = resolver(usage);
  }

  return {
    name: product.name,
    description: product.description,
    project_types: projectTypes,
    stage: product.stage === "production" ? "mvp" : product.stage || "mvp",
    expected_users: resolveExpectedUsers(usage),
    answers,
    usage_profile: buildUsageProfile(usage),
  };
}
