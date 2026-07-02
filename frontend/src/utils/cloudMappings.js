const PROVIDERS = ["aws", "gcp", "azure"];

export function selectedCloudService(value) {
  if (Array.isArray(value)) {
    value = value.find((item) => String(item || "").trim());
  }
  const text = String(value || "").trim();
  return text || null;
}

export function normalizeCloudMappings(componentOrMappings) {
  const mappings =
    componentOrMappings?.cloud_mappings ||
    componentOrMappings?.cloud_mapping ||
    componentOrMappings ||
    {};

  return Object.fromEntries(
    PROVIDERS.map((provider) => [provider, selectedCloudService(mappings[provider])])
  );
}
