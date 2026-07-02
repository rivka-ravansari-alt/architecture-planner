import {
  COMPONENT_SOURCE_USER,
  formatComponentTypeLabel,
  getComponentTypeDescription,
  normalizeComponentType,
} from "../constants/componentTypes.js";
import {
  getCatalogCloudMapping,
  getCatalogTypeNames,
  getDefaultCatalogType,
} from "../constants/componentCatalog.js";
import { normalizeCloudMappings } from "./cloudMappings.js";

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
  const defaultType = getDefaultCatalogType();
  return {
    name: formatComponentTypeLabel(defaultType),
    type: defaultType,
    reason: getComponentTypeDescription(defaultType),
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
    type: component?.type || getDefaultCatalogType(),
    reason: component?.reason || "",
    optional: Boolean(component?.optional),
  };
}

export function validateComponentForm(form) {
  const errors = {};
  const reason = form.reason.trim();
  const catalogTypes = getCatalogTypeNames();

  if (!form.type || !catalogTypes.includes(form.type)) {
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
  const cloudMapping =
    typeChanged || !currentComponent
      ? getCatalogCloudMapping(form.type)
      : normalizeCloudMappings(currentComponent) || getCatalogCloudMapping(form.type);

  return {
    key,
    name,
    type: form.type,
    reason,
    optional: Boolean(form.optional),
    source: currentComponent?.source || COMPONENT_SOURCE_USER,
    cloud_mappings: cloudMapping,
  };
}

function normalizeFormType(type) {
  return String(type || "").trim().toLowerCase();
}
