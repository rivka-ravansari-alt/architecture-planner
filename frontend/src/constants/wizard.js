export const WIZARD_STEPS = [
  "Product Info",
  "Architecture",
  "Component Review",
  "Architecture Document",
];

export const STEP_SUBTITLES = [
  "Basic product details that shape platform choice and scale.",
  "Toggle only the capabilities that affect infrastructure and cost.",
  "Review, adjust, and approve the generated architecture components.",
  "Review diagrams and flow, then generate cloud pricing when ready.",
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

export const WORKFLOW_STATUS = {
  DRAFT: "DRAFT",
  COMPONENTS_GENERATED: "COMPONENTS_GENERATED",
  COMPONENTS_APPROVED: "COMPONENTS_APPROVED",
  DIAGRAMS_GENERATED: "DIAGRAMS_GENERATED",
  ARCHITECTURE_APPROVED: "ARCHITECTURE_APPROVED",
  PRICING_GENERATED: "PRICING_GENERATED",
};

export const WORKFLOW_STATUS_LABELS = {
  [WORKFLOW_STATUS.DRAFT]: "Draft",
  [WORKFLOW_STATUS.COMPONENTS_GENERATED]: "Components generated",
  [WORKFLOW_STATUS.COMPONENTS_APPROVED]: "Components approved",
  [WORKFLOW_STATUS.DIAGRAMS_GENERATED]: "Diagrams generated",
  [WORKFLOW_STATUS.ARCHITECTURE_APPROVED]: "Architecture approved",
  [WORKFLOW_STATUS.PRICING_GENERATED]: "Pricing generated",
};

export const STALE_NOTICE_TEXT =
  "You've changed your inputs. Save the project again and regenerate components when you continue.";

export const AUTH_ROUTES = {
  googleLogin: "/api/auth/google",
};
