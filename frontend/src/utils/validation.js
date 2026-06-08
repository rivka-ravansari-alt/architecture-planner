import { DESCRIPTION_MAX_CHARS } from "../constants/wizard.js";

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

  if (!String(product.expected_users || "").trim()) {
    errors.expected_users = "Expected users is required.";
  }

  return errors;
}

/** @deprecated Use validateBasicProduct */
export function validateProjectForm(form) {
  return validateBasicProduct({ product: form, features: {} });
}

/**
 * @param {ReturnType<import("./intakeFormState.js").createEmptyIntakeForm>} intakeForm
 */
export function buildInputKey(intakeForm) {
  return JSON.stringify(intakeForm);
}
