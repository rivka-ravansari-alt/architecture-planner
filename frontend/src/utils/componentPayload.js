import { normalizeCloudMappings } from "./cloudMappings.js";

export function componentsToApiPayload(components) {
  return components.map((component) => {
    const cloudMapping = normalizeCloudMappings(component);

    return {
      key: component.key,
      name: component.name,
      type: component.type,
      reason: component.reason || "",
      optional: Boolean(component.optional),
      source: component.source || "ai_generated",
      cloud_mappings: {
        aws: cloudMapping.aws,
        gcp: cloudMapping.gcp,
        azure: cloudMapping.azure,
      },
    };
  });
}
