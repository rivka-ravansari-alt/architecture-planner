export function componentsToApiPayload(components) {
  return components.map((component) => ({
    key: component.key,
    name: component.name,
    type: component.type,
    reason: component.reason || "",
    optional: Boolean(component.optional),
    source: component.source || "ai_generated",
    cloud_mapping: component.cloud_mapping
      ? {
          aws: component.cloud_mapping.aws || [],
          gcp: component.cloud_mapping.gcp || [],
          azure: component.cloud_mapping.azure || [],
        }
      : { aws: [], gcp: [], azure: [] },
    implementation_options: component.implementation_options || null,
  }));
}
