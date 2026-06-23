import {
  CATALOG_COMPONENT_TYPES,
  COMPONENT_SOURCE_USER,
  DEFAULT_COMPONENT_TYPE,
  formatComponentTypeLabel,
  getComponentTypeDescription,
} from "../constants/componentTypes.js";

export function slugifyComponentName(name) {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 60) || "component"
  );
}

export function uniqueComponentKey(name, existingKeys, currentKey = null) {
  if (currentKey) {
    return currentKey;
  }
  const base = slugifyComponentName(name);
  let candidate = base;
  let suffix = 2;
  while (existingKeys.has(candidate)) {
    candidate = `${base}_${suffix}`;
    suffix += 1;
  }
  return candidate;
}

export function emptyComponentForm() {
  return {
    name: formatComponentTypeLabel(DEFAULT_COMPONENT_TYPE),
    type: DEFAULT_COMPONENT_TYPE,
    reason: getComponentTypeDescription(DEFAULT_COMPONENT_TYPE),
    optional: false,
  };
}

export function resolveComponentName(form) {
  const trimmed = form.name.trim();
  if (trimmed) {
    return trimmed;
  }
  return formatComponentTypeLabel(form.type);
}

export function applyTypeDescription(form, nextType) {
  const previousDefaultReason = getComponentTypeDescription(form.type);
  const previousDefaultName = formatComponentTypeLabel(form.type);
  const shouldReplaceReason =
    !form.reason.trim() || form.reason.trim() === previousDefaultReason.trim();
  const shouldReplaceName =
    !form.name.trim() || form.name.trim() === previousDefaultName.trim();

  return {
    ...form,
    type: nextType,
    name: shouldReplaceName ? formatComponentTypeLabel(nextType) : form.name,
    reason: shouldReplaceReason ? getComponentTypeDescription(nextType) : form.reason,
  };
}

export function componentToForm(component) {
  return {
    name: component?.name || "",
    type: component?.type || DEFAULT_COMPONENT_TYPE,
    reason: component?.reason || "",
    optional: Boolean(component?.optional),
  };
}

export function validateComponentForm(form) {
  const errors = {};
  const reason = form.reason.trim();

  if (!form.type || !CATALOG_COMPONENT_TYPES.includes(form.type)) {
    errors.type = "Select a component type.";
  }
  if (!reason) {
    errors.reason = "Describe what this component is used for.";
  }

  return errors;
}

export function buildComponentFromForm(form, { existingKeys, currentComponent = null }) {
  const name = resolveComponentName(form);
  const reason = form.reason.trim();
  const key = uniqueComponentKey(name, existingKeys, currentComponent?.key ?? null);
  const typeChanged =
    currentComponent && normalizeFormType(form.type) !== normalizeFormType(currentComponent.type);

  return {
    key,
    name,
    type: form.type,
    reason,
    optional: Boolean(form.optional),
    source: currentComponent?.source || COMPONENT_SOURCE_USER,
    cloud_mapping: typeChanged
      ? { aws: [], gcp: [], azure: [] }
      : currentComponent?.cloud_mapping || { aws: [], gcp: [], azure: [] },
    implementation_options: currentComponent?.implementation_options ?? null,
  };
}

function normalizeFormType(type) {
  return String(type || "").trim().toLowerCase();
}
