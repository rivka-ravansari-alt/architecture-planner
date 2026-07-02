let catalogEntries = [];

export function setComponentCatalog(entries) {
  catalogEntries = Array.isArray(entries) ? entries : [];
}

export function getComponentCatalogEntries() {
  return catalogEntries;
}

export function getCatalogTypeNames() {
  return catalogEntries.map((entry) => entry.name);
}

export function getCatalogDescription(type) {
  const normalized = String(type || "").trim().toLowerCase();
  const entry = catalogEntries.find((item) => item.name === normalized);
  return entry?.description || null;
}

export function getCatalogCloudMapping(type) {
  const normalized = String(type || "").trim().toLowerCase();
  const entry = catalogEntries.find((item) => item.name === normalized);
  return {
    aws: firstMapping(entry?.aws_options),
    gcp: firstMapping(entry?.gcp_options),
    azure: firstMapping(entry?.azure_options),
  };
}

function firstMapping(options) {
  if (!Array.isArray(options)) {
    return null;
  }
  const selected = options.find((option) => String(option || "").trim());
  return selected ? String(selected).trim() : null;
}

export function getDefaultCatalogType() {
  if (catalogEntries.some((entry) => entry.name === "api_gateway")) {
    return "api_gateway";
  }
  return catalogEntries[0]?.name || "api_gateway";
}
