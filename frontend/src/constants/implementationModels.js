export const IMPLEMENTATION_MODEL_KEYS = [
  "serverless",
  "container",
  "managed_service",
  "external_provider",
];

export const IMPLEMENTATION_MODEL_LABELS = {
  serverless: "Serverless",
  container: "Container / Server",
  managed_service: "Managed Service",
  external_provider: "External Provider",
};

export function normalizeOptionDetail(raw) {
  if (!raw) return null;

  if (typeof raw === "string") {
    const whenToUse = raw.trim();
    if (!whenToUse) return null;
    const notApplicable = /^not applicable/i.test(whenToUse);
    return {
      when_to_use: whenToUse,
      cost_impact: notApplicable ? "" : "Varies with usage and scale.",
      pros: [],
      cons: [],
      not_applicable: notApplicable,
    };
  }

  if (typeof raw === "object") {
    const whenToUse = String(raw.when_to_use || "").trim();
    if (!whenToUse) return null;
    return {
      when_to_use: whenToUse,
      cost_impact: String(raw.cost_impact || "").trim(),
      pros: Array.isArray(raw.pros) ? raw.pros.filter(Boolean) : [],
      cons: Array.isArray(raw.cons) ? raw.cons.filter(Boolean) : [],
      not_applicable:
        Boolean(raw.not_applicable) || /^not applicable/i.test(whenToUse),
    };
  }

  return null;
}

export function getImplementationOptionEntries(implementationOptions) {
  if (!implementationOptions) return [];

  return IMPLEMENTATION_MODEL_KEYS.map((key) => ({
    key,
    label: IMPLEMENTATION_MODEL_LABELS[key],
    detail: normalizeOptionDetail(implementationOptions[key]),
  })).filter((entry) => entry.detail);
}
