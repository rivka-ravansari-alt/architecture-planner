import { INTAKE_FORM_CONFIG } from "../config/intakeFormConfig.js";

const { productSection, architectureSection } = INTAKE_FORM_CONFIG;

/** @param {import("../config/intakeFormConfig.js").FormField} field */
function defaultFieldValue(field) {
  if (field.defaultValue !== undefined) {
    return field.defaultValue;
  }

  switch (field.type) {
    case "checkbox_group":
    case "multi_select":
      return [];
    case "boolean":
      return false;
    default:
      return "";
  }
}

/** @param {import("../config/intakeFormConfig.js").FeatureToggle} toggle */
function createFeatureState(toggle) {
  /** @type {Record<string, unknown>} */
  const feature = { enabled: false };
  for (const field of toggle.fields) {
    feature[field.key] = defaultFieldValue(field);
  }
  return feature;
}

export function createEmptyIntakeForm() {
  /** @type {Record<string, unknown>} */
  const product = {};
  for (const field of productSection.fields) {
    product[field.key] = defaultFieldValue(field);
  }

  /** @type {Record<string, Record<string, unknown>>} */
  const features = {};
  for (const toggle of architectureSection.toggles) {
    features[toggle.key] = createFeatureState(toggle);
  }

  return { product, features };
}

export const EMPTY_INTAKE_FORM = createEmptyIntakeForm();

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @returns {ReturnType<typeof createEmptyIntakeForm>}
 */
export function buildIntakeOutput(intakeForm) {
  return JSON.parse(JSON.stringify(intakeForm));
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string[]} path
 * @param {unknown} value
 */
export function setIntakeValue(intakeForm, path, value) {
  const next = JSON.parse(JSON.stringify(intakeForm));
  let cursor = next;
  for (let index = 0; index < path.length - 1; index += 1) {
    cursor = cursor[path[index]];
  }
  cursor[path[path.length - 1]] = value;
  return next;
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string} featureKey
 * @param {boolean} enabled
 */
export function setFeatureEnabled(intakeForm, featureKey, enabled) {
  const toggle = architectureSection.toggles.find((item) => item.key === featureKey);
  if (!toggle) return intakeForm;

  let next = setIntakeValue(intakeForm, ["features", featureKey, "enabled"], enabled);

  if (!enabled) {
    for (const field of toggle.fields) {
      next = setIntakeValue(next, ["features", featureKey, field.key], defaultFieldValue(field));
    }
  }

  return next;
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string} fieldKey
 * @param {unknown} value
 */
export function setProductField(intakeForm, fieldKey, value) {
  return setIntakeValue(intakeForm, ["product", fieldKey], value);
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string} featureKey
 * @param {string} fieldKey
 * @param {unknown} value
 */
export function setFeatureField(intakeForm, featureKey, fieldKey, value) {
  return setIntakeValue(intakeForm, ["features", featureKey, fieldKey], value);
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string} fieldKey
 * @param {string} optionValue
 */
export function togglePlatform(intakeForm, fieldKey, optionValue) {
  const current = intakeForm.product[fieldKey];
  const platforms = Array.isArray(current) ? [...current] : [];

  if (optionValue === "both") {
    const hasBoth = platforms.includes("web") && platforms.includes("mobile");
    return setProductField(
      intakeForm,
      fieldKey,
      hasBoth ? [] : ["web", "mobile"]
    );
  }

  const exists = platforms.includes(optionValue);
  const nextPlatforms = exists
    ? platforms.filter((item) => item !== optionValue)
    : [...platforms, optionValue];

  return setProductField(intakeForm, fieldKey, nextPlatforms);
}

/**
 * @param {string[]} values
 * @param {string} optionValue
 */
export function isPlatformSelected(values, optionValue) {
  if (optionValue === "both") {
    return values.includes("web") && values.includes("mobile");
  }
  return values.includes(optionValue);
}
