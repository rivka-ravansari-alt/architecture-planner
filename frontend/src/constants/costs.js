export const COST_PROVIDERS = ["aws", "gcp", "azure"];

export const COST_BASELINE = { aws: [15, 45], gcp: [12, 40], azure: [18, 50] };

export const COST_FEATURE_BANDS = {
  object_storage: { aws: [5, 20], gcp: [4, 18], azure: [5, 22] },
  ai_service: { aws: [20, 120], gcp: [18, 110], azure: [22, 130] },
  queue_worker: { aws: [8, 30], gcp: [7, 28], azure: [9, 32] },
};

export const COST_OPTIONAL_INFRA_BANDS = {
  cdn: { aws: [5, 25], gcp: [4, 22], azure: [5, 26] },
  database: { aws: [10, 40], gcp: [9, 36], azure: [11, 44] },
  api_layer: { aws: [8, 30], gcp: [7, 27], azure: [9, 33] },
};

export const COST_PRODUCTION_BAND = { aws: [15, 60], gcp: [12, 55], azure: [16, 65] };

export const COST_USER_MULTIPLIER = {
  100: 1.0,
  1000: 1.8,
  10000: 4.0,
  "100000+": 9.0,
};

export const COST_PRODUCTION_KEYS = new Set([
  "monitoring",
  "logging",
  "backup",
  "alerts",
  "security",
]);

export const COST_CURRENCY = "USD";
