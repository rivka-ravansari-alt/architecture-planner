import {
  COST_BASELINE,
  COST_CURRENCY,
  COST_FEATURE_BANDS,
  COST_OPTIONAL_INFRA_BANDS,
  COST_PRODUCTION_BAND,
  COST_PRODUCTION_KEYS,
  COST_PROVIDERS,
  COST_USER_MULTIPLIER,
} from "../../../constants/costs.js";

function bandFor(component, provider) {
  if (COST_PRODUCTION_KEYS.has(component.key)) return null;
  if (component.optional && COST_OPTIONAL_INFRA_BANDS[component.key]) {
    return COST_OPTIONAL_INFRA_BANDS[component.key][provider];
  }
  if (COST_FEATURE_BANDS[component.key]) return COST_FEATURE_BANDS[component.key][provider];
  return null;
}

export function computeCosts(project, components) {
  const multiplier = COST_USER_MULTIPLIER[project.expected_users] ?? 1.0;
  const hasRequired = components.some((component) => !component.optional);
  const reqProd = components.some(
    (component) => !component.optional && COST_PRODUCTION_KEYS.has(component.key)
  );
  const optProd = components.some(
    (component) => component.optional && COST_PRODUCTION_KEYS.has(component.key)
  );

  return COST_PROVIDERS.map((provider) => {
    let reqLow = 0;
    let reqHigh = 0;
    let optLow = 0;
    let optHigh = 0;

    if (hasRequired) {
      reqLow += COST_BASELINE[provider][0];
      reqHigh += COST_BASELINE[provider][1];
    }
    if (reqProd) {
      reqLow += COST_PRODUCTION_BAND[provider][0];
      reqHigh += COST_PRODUCTION_BAND[provider][1];
    } else if (optProd) {
      optLow += COST_PRODUCTION_BAND[provider][0];
      optHigh += COST_PRODUCTION_BAND[provider][1];
    }

    for (const component of components) {
      const band = bandFor(component, provider);
      if (!band) continue;
      if (component.optional) {
        optLow += band[0];
        optHigh += band[1];
      } else {
        reqLow += band[0];
        reqHigh += band[1];
      }
    }

    const scale = (value) => Math.round(value * multiplier);
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
      currency: COST_CURRENCY,
    };
  });
}

export function deriveArchitecture(project, components) {
  return {
    costs: computeCosts(project, components),
  };
}
