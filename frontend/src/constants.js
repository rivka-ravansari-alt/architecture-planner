export const STAGES = [
  { id: "mvp", label: "MVP" },
  { id: "production", label: "Production" },
];

export const EXPECTED_USERS = [
  { id: "100", label: "Up to 100" },
  { id: "1000", label: "Up to 1,000" },
  { id: "10000", label: "Up to 10,000" },
  { id: "100000+", label: "100,000+" },
];

export const REQUIREMENTS = [
  { key: "auth", label: "Does the system need authentication?" },
  { key: "file_upload", label: "Does the system upload files?" },
  { key: "background_processing", label: "Does the system need background processing?" },
  { key: "dashboards", label: "Does the system need dashboards or reports?" },
  { key: "ai", label: "Does the system use AI?" },
  { key: "payments", label: "Does the system need payments?" },
  { key: "include_edge_cases", label: "Should edge cases be included?" },
];

export const STEPS = [
  "Project Details",
  "Requirements",
  "Architecture Document",
];

export const DESCRIPTION_MAX_TOKENS = 500;

export function estimateTokenCount(text) {
  const stripped = text.trim();
  if (!stripped) return 0;
  return Math.max(1, Math.ceil(stripped.length / 4));
}

export const PROVIDER_LABELS = {
  aws: "AWS",
  gcp: "Google Cloud",
  azure: "Azure",
};
