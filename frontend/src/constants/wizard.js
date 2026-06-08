export const WIZARD_STEPS = [
  "Product Info",
  "Architecture",
  "Architecture Document",
];

export const STEP_SUBTITLES = [
  "Basic product details that shape platform choice and scale.",
  "Toggle only the capabilities that affect infrastructure and cost.",
  "Review your AI-generated architecture document and refine the plan.",
];

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

export const DESCRIPTION_MAX_CHARS = 1200;

export const EMPTY_FORM = {
  name: "",
  description: "",
  project_types: [],
  stage: "mvp",
  expected_users: "100",
};

export const EMPTY_ANSWERS = {
  auth: false,
  file_upload: false,
  background_processing: false,
  dashboards: false,
  ai: false,
  payments: false,
  include_edge_cases: false,
};

export const STALE_NOTICE_TEXT =
  "You've changed your inputs. The architecture, cloud mapping, and cost estimates will be regenerated when you open the Architecture Document.";

export const AUTH_ROUTES = {
  googleLogin: "/api/auth/google",
};
