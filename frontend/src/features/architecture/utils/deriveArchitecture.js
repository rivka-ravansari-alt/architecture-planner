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

function computeHeuristicCosts(project, components) {
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
      source: "heuristic",
    };
  });
}

function componentSubtotal(component) {
  const direct = Number(component.subtotal_usd ?? 0);
  if (direct > 0) {
    return direct;
  }
  return (component.line_items ?? []).reduce(
    (sum, line) => sum + Number(line.monthly_cost_usd ?? 0),
    0
  );
}

function buildOptionalLookup(project, wizardComponents) {
  const lookup = new Map();
  for (const component of [...(project?.components ?? []), ...wizardComponents]) {
    if (component?.key != null) {
      lookup.set(component.key, Boolean(component.optional));
    }
  }
  return lookup;
}

function isOptionalCostComponent(pricingComponent, optionalLookup) {
  if (pricingComponent.optional === true) {
    return true;
  }
  if (pricingComponent.optional === false) {
    return false;
  }
  return optionalLookup.get(pricingComponent.component_id) === true;
}

function splitCatalogCostByOptional(estimate, project, wizardComponents) {
  const detail = estimate.pricing_detail ?? null;
  const fallbackLow = Number(estimate.monthly_low ?? 0);
  const fallbackHigh = Number(estimate.monthly_high ?? fallbackLow);

  if (!detail?.components?.length) {
    return {
      requiredLow: fallbackLow,
      requiredHigh: fallbackHigh,
      optionalLow: 0,
      optionalHigh: 0,
      totalLow: fallbackLow,
      totalHigh: fallbackHigh,
    };
  }

  const optionalLookup = buildOptionalLookup(project, wizardComponents);
  let requiredTotal = 0;
  let optionalTotal = 0;

  for (const component of detail.components) {
    const amount = componentSubtotal(component);
    if (isOptionalCostComponent(component, optionalLookup)) {
      optionalTotal += amount;
    } else {
      requiredTotal += amount;
    }
  }

  const splitTotal = requiredTotal + optionalTotal;
  const totalLow = splitTotal > 0 ? splitTotal : fallbackLow;
  const totalHigh = splitTotal > 0 ? splitTotal : fallbackHigh;

  return {
    requiredLow: requiredTotal,
    requiredHigh: requiredTotal,
    optionalLow: optionalTotal,
    optionalHigh: optionalTotal,
    totalLow,
    totalHigh,
  };
}

function costFromApiEstimate(estimate, project, wizardComponents) {
  const split = splitCatalogCostByOptional(estimate, project, wizardComponents);
  const pricingDetail = estimate.pricing_detail ?? null;

  return {
    provider: estimate.provider,
    requiredLow: split.requiredLow,
    requiredHigh: split.requiredHigh,
    optionalLow: split.optionalLow,
    optionalHigh: split.optionalHigh,
    totalLow: split.totalLow,
    totalHigh: split.totalHigh,
    monthly_low: estimate.monthly_low ?? split.totalLow,
    monthly_high: estimate.monthly_high ?? split.totalHigh,
    currency: estimate.currency ?? COST_CURRENCY,
    notes: estimate.notes ?? "",
    pricingDetail,
    pricing_detail: pricingDetail,
    source: pricingDetail ? "catalog" : "heuristic",
  };
}

export function computeCosts(project, components) {
  const apiEstimates = project?.cost_estimates ?? [];
  const hasApiPricing = apiEstimates.length > 0;

  if (hasApiPricing) {
    const byProvider = new Map(apiEstimates.map((estimate) => [estimate.provider, estimate]));
    return COST_PROVIDERS.map((provider) => {
      const estimate = byProvider.get(provider);
      if (estimate) {
        return costFromApiEstimate(estimate, project, components);
      }
      return computeHeuristicCosts(project, components).find((cost) => cost.provider === provider);
    });
  }

  return computeHeuristicCosts(project, components);
}

export function deriveArchitecture(project, components) {
  return {
    costs: computeCosts(project, components),
  };
}
