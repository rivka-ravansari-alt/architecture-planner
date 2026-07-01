import { INTAKE_FORM_CONFIG } from "../config/intakeFormConfig.js";

const { productSection, usageSection } = INTAKE_FORM_CONFIG;

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
    case "number":
      return "";
    default:
      return "";
  }
}

/** @param {import("../config/intakeFormConfig.js").UsageToggleGroup} toggle */
function createUsageToggleState(toggle) {
  /** @type {Record<string, unknown>} */
  const group = { enabled: false };
  for (const field of toggle.fields) {
    group[field.key] = defaultFieldValue(field);
  }
  return group;
}

export function createEmptyIntakeForm() {
  /** @type {Record<string, unknown>} */
  const product = {};
  for (const field of productSection.fields) {
    product[field.key] = defaultFieldValue(field);
  }

  /** @type {Record<string, unknown>} */
  const usage = {};
  for (const block of usageSection.questionBlocks) {
    for (const field of block.fields) {
      usage[field.key] = defaultFieldValue(field);
    }
  }
  for (const toggle of usageSection.toggleGroups) {
    usage[toggle.key] = createUsageToggleState(toggle);
  }

  return { product, usage };
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
 * @param {string} toggleKey
 * @param {boolean} enabled
 */
export function setUsageToggleEnabled(intakeForm, toggleKey, enabled) {
  const toggle = usageSection.toggleGroups.find((item) => item.key === toggleKey);
  if (!toggle) return intakeForm;

  let next = setIntakeValue(intakeForm, ["usage", toggleKey, "enabled"], enabled);

  if (!enabled) {
    for (const field of toggle.fields) {
      next = setIntakeValue(
        next,
        ["usage", toggleKey, field.key],
        defaultFieldValue(field)
      );
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
 * @param {string} fieldKey
 * @param {unknown} value
 */
export function setUsageField(intakeForm, fieldKey, value) {
  return setIntakeValue(intakeForm, ["usage", fieldKey], value);
}

/**
 * @param {ReturnType<typeof createEmptyIntakeForm>} intakeForm
 * @param {string} toggleKey
 * @param {string} fieldKey
 * @param {unknown} value
 */
export function setUsageToggleField(intakeForm, toggleKey, fieldKey, value) {
  return setIntakeValue(intakeForm, ["usage", toggleKey, fieldKey], value);
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
