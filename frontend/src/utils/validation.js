import { DESCRIPTION_MAX_CHARS } from "../constants/wizard.js";
import { INTAKE_FORM_CONFIG } from "../config/intakeFormConfig.js";

const { usageSection } = INTAKE_FORM_CONFIG;

export function estimateTokenCount(text) {
  const stripped = text.trim();
  if (!stripped) return 0;
  return Math.max(1, Math.ceil(stripped.length / 4));
}

/**
 * Validates required basic product fields only.
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function validateBasicProduct(intakeForm) {
  const { product } = intakeForm;
  /** @type {Record<string, string>} */
  const errors = {};

  if (!String(product.name || "").trim()) {
    errors.name = "Product name is required.";
  }

  const description = String(product.description || "");
  if (!description.trim()) {
    errors.description = "Product description is required.";
  } else if (description.length > DESCRIPTION_MAX_CHARS) {
    errors.description = `Product description must be ${DESCRIPTION_MAX_CHARS} characters or fewer.`;
  }

  const platforms = Array.isArray(product.platforms) ? product.platforms : [];
  if (platforms.length === 0) {
    errors.platforms = "Select at least one platform.";
  }

  if (!String(product.stage || "").trim()) {
    errors.stage = "Stage is required.";
  }

  return errors;
}

/**
 * Validates required usage profile fields for the Requirements step.
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function validateUsageProfile(intakeForm) {
  const { usage } = intakeForm;
  /** @type {Record<string, string>} */
  const errors = {};

  for (const fieldKey of usageSection.validation) {
    if (!String(usage[fieldKey] || "").trim()) {
      const block = usageSection.questionBlocks.find((item) =>
        item.fields.some((field) => field.key === fieldKey)
      );
      const field = block?.fields.find((item) => item.key === fieldKey);
      errors[fieldKey] = `${field?.label || block?.title || fieldKey} is required.`;
    }
  }

  if (usage.monthly_active_users === "custom") {
    const custom = Number(usage.custom_monthly_active_users);
    if (!Number.isFinite(custom) || custom < 1) {
      errors.custom_monthly_active_users = "Enter a valid number of monthly active users.";
    }
  }

  return errors;
}

/**
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function validateIntakeForm(intakeForm) {
  return {
    ...validateBasicProduct(intakeForm),
    ...validateUsageProfile(intakeForm),
  };
}

/** @deprecated Use validateBasicProduct */
export function validateProjectForm(form) {
  return validateBasicProduct({ product: form, usage: {} });
}

/**
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function buildInputKey(intakeForm) {
  return JSON.stringify(intakeForm);
}
