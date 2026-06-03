/**
 * Recompute cost estimates when the user toggles Required vs Optional.
 * Risks and recommendations come from the AI-generated project payload.
 */

const PROVIDERS = ["aws", "gcp", "azure"];
const BASELINE = { aws: [15, 45], gcp: [12, 40], azure: [18, 50] };
const FEATURE_BANDS = {
  object_storage: { aws: [5, 20], gcp: [4, 18], azure: [5, 22] },
  ai_service: { aws: [20, 120], gcp: [18, 110], azure: [22, 130] },
  queue_worker: { aws: [8, 30], gcp: [7, 28], azure: [9, 32] },
};
const OPTIONAL_INFRA_BANDS = {
  cdn: { aws: [5, 25], gcp: [4, 22], azure: [5, 26] },
  database: { aws: [10, 40], gcp: [9, 36], azure: [11, 44] },
  api_layer: { aws: [8, 30], gcp: [7, 27], azure: [9, 33] },
};
const PRODUCTION_BAND = { aws: [15, 60], gcp: [12, 55], azure: [16, 65] };
const USER_MULTIPLIER = { 100: 1.0, 1000: 1.8, 10000: 4.0, "100000+": 9.0 };
const PRODUCTION_KEYS = new Set(["monitoring", "logging", "backup", "alerts", "security"]);

function bandFor(component, provider) {
  if (PRODUCTION_KEYS.has(component.key)) return null;
  if (component.optional && OPTIONAL_INFRA_BANDS[component.key]) {
    return OPTIONAL_INFRA_BANDS[component.key][provider];
  }
  if (FEATURE_BANDS[component.key]) return FEATURE_BANDS[component.key][provider];
  return null;
}

export function computeCosts(project, components) {
  const multiplier = USER_MULTIPLIER[project.expected_users] ?? 1.0;
  const hasRequired = components.some((c) => !c.optional);
  const reqProd = components.some((c) => !c.optional && PRODUCTION_KEYS.has(c.key));
  const optProd = components.some((c) => c.optional && PRODUCTION_KEYS.has(c.key));

  return PROVIDERS.map((provider) => {
    let reqLow = 0;
    let reqHigh = 0;
    let optLow = 0;
    let optHigh = 0;

    if (hasRequired) {
      reqLow += BASELINE[provider][0];
      reqHigh += BASELINE[provider][1];
    }
    if (reqProd) {
      reqLow += PRODUCTION_BAND[provider][0];
      reqHigh += PRODUCTION_BAND[provider][1];
    } else if (optProd) {
      optLow += PRODUCTION_BAND[provider][0];
      optHigh += PRODUCTION_BAND[provider][1];
    }

    for (const c of components) {
      const band = bandFor(c, provider);
      if (!band) continue;
      if (c.optional) {
        optLow += band[0];
        optHigh += band[1];
      } else {
        reqLow += band[0];
        reqHigh += band[1];
      }
    }

    const scale = (n) => Math.round(n * multiplier);
    const requiredLow = scale(reqLow);
    const requiredHigh = scale(reqHigh);
    const optionalLow = scale(optLow);
    const optionalHigh = scale(optHigh);

    return {
      provider,
      requiredLow,
      requiredHigh,
      optionalLow,
      optionalHigh,
      totalLow: requiredLow + optionalLow,
      totalHigh: requiredHigh + optionalHigh,
      currency: "USD",
    };
  });
}

export function deriveArchitecture(project, components) {
  return {
    risks: (project.risks || []).map((r) => ({
      title: r.title,
      description: r.description,
      severity: r.severity,
    })),
    recommendations: (project.recommendations || []).map((r) => r.text || r),
    costs: computeCosts(project, components),
  };
}
