/**
 * Static sample data used to render the UI without any backend/AI functionality.
 * These values replace what the AI generation pipeline used to produce, so the
 * architecture document and diagram screens still render as a visual template.
 */

export const SAMPLE_USER = {
  id: "demo-user",
  email: "demo@archsari.app",
  name: "Demo User",
  picture: "",
};

export const SAMPLE_PROJECT_TYPES = [
  { id: "web_app", label: "Web App" },
  { id: "mobile_app", label: "Mobile App" },
];

function implementationOptions(recommended, overrides = {}) {
  const base = {
    recommended,
    serverless: {
      when_to_use: "Low or spiky traffic with minimal operations overhead.",
      cost_impact: "Very low at MVP scale; pay per use.",
      pros: ["Minimal ops", "Automatic scaling"],
      cons: ["Cold starts", "Execution limits"],
    },
    container: {
      when_to_use: "Steady, predictable traffic where always-on compute is cost-effective.",
      cost_impact: "Moderate baseline; can beat serverless at steady load.",
      pros: ["Consistent performance", "Long-running workloads"],
      cons: ["Higher idle cost", "More deployment work"],
    },
    managed_service: {
      when_to_use: "Default choice when a fully managed platform fits the workload.",
      cost_impact: "Low-to-moderate fixed monthly cost for small workloads.",
      pros: ["Fast to ship", "Built-in maintenance"],
      cons: ["Less fine-grained control"],
    },
    external_provider: {
      when_to_use: "Third-party SaaS or API when outsourcing is the best fit.",
      cost_impact: "Usage-based or subscription pricing from the vendor.",
      pros: ["Fast integration", "Vendor handles compliance and uptime"],
      cons: ["Vendor lock-in", "Per-seat or API pricing can grow"],
    },
  };
  return { ...base, ...overrides };
}

const notApplicable = {
  when_to_use: "Not applicable for this component.",
  cost_impact: "",
  pros: [],
  cons: [],
  not_applicable: true,
};

export const SAMPLE_COMPONENTS = [
  {
    key: "web_client",
    name: "Web Client",
    type: "web_app",
    optional: false,
    reason: "Provides the user interface for interacting with the product.",
    implementation_options: implementationOptions("managed_service", {
      serverless: notApplicable,
      external_provider: notApplicable,
    }),
    cloud_mapping: {
      aws: ["Amplify Hosting"],
      gcp: ["Firebase Hosting"],
      azure: ["Azure Static Web Apps"],
    },
  },
  {
    key: "api_layer",
    name: "Backend / API Layer",
    type: "api",
    optional: false,
    reason: "Central entry point for client requests and service routing.",
    implementation_options: implementationOptions("serverless", {
      external_provider: notApplicable,
    }),
    cloud_mapping: {
      aws: ["API Gateway"],
      gcp: ["API Gateway"],
      azure: ["API Management"],
    },
  },
  {
    key: "app_service",
    name: "Application Service",
    type: "service",
    optional: true,
    reason: "Runs core business logic when separated from the API tier.",
    implementation_options: implementationOptions("serverless"),
    cloud_mapping: {
      aws: ["Lambda", "ECS Fargate"],
      gcp: ["Cloud Run", "Cloud Functions"],
      azure: ["Azure Functions", "Container Apps"],
    },
  },
  {
    key: "authentication",
    name: "Authentication Service",
    type: "authentication",
    optional: false,
    reason: "Handles user sign-up, login, and session management.",
    implementation_options: implementationOptions("managed_service", {
      serverless: notApplicable,
      container: notApplicable,
    }),
    cloud_mapping: {
      aws: ["Cognito"],
      gcp: ["Firebase Authentication", "Identity Platform"],
      azure: ["Entra ID B2C"],
    },
  },
  {
    key: "database",
    name: "Database",
    type: "database",
    optional: false,
    reason: "Stores application data with durable, queryable persistence.",
    implementation_options: implementationOptions("managed_service", {
      external_provider: notApplicable,
    }),
    cloud_mapping: {
      aws: ["DynamoDB", "RDS"],
      gcp: ["Firestore", "Cloud SQL"],
      azure: ["Cosmos DB", "Azure SQL Database"],
    },
  },
  {
    key: "object_storage",
    name: "Object Storage",
    type: "object_storage",
    optional: true,
    reason: "Stores uploaded files and static assets when file uploads are needed.",
    implementation_options: implementationOptions("managed_service", {
      serverless: notApplicable,
      container: notApplicable,
      external_provider: notApplicable,
    }),
    cloud_mapping: {
      aws: ["S3"],
      gcp: ["Cloud Storage"],
      azure: ["Blob Storage"],
    },
  },
  {
    key: "worker",
    name: "Background Worker",
    type: "worker",
    optional: true,
    reason: "Processes long-running or async jobs outside the request path.",
    implementation_options: implementationOptions("serverless"),
    cloud_mapping: {
      aws: ["Lambda", "ECS Fargate"],
      gcp: ["Cloud Run Jobs", "Cloud Functions"],
      azure: ["Azure Functions", "Container Apps Jobs"],
    },
  },
  {
    key: "monitoring",
    name: "Monitoring and Logging",
    type: "monitoring",
    optional: true,
    reason: "Tracks health, metrics, and logs for production operations.",
    implementation_options: implementationOptions("managed_service", {
      serverless: notApplicable,
      container: notApplicable,
      external_provider: notApplicable,
    }),
    cloud_mapping: {
      aws: ["CloudWatch"],
      gcp: ["Cloud Monitoring"],
      azure: ["Azure Monitor"],
    },
  },
];

export const SAMPLE_COSTS = [
  {
    provider: "aws",
    requiredLow: 58,
    requiredHigh: 205,
    optionalLow: 23,
    optionalHigh: 90,
    totalLow: 81,
    totalHigh: 295,
    currency: "USD",
  },
  {
    provider: "gcp",
    requiredLow: 50,
    requiredHigh: 185,
    optionalLow: 20,
    optionalHigh: 82,
    totalLow: 70,
    totalHigh: 267,
    currency: "USD",
  },
  {
    provider: "azure",
    requiredLow: 63,
    requiredHigh: 222,
    optionalLow: 25,
    optionalHigh: 98,
    totalLow: 88,
    totalHigh: 320,
    currency: "USD",
  },
];

export const SAMPLE_PROJECT = {
  id: "demo-project",
  name: "Task Manager",
  description: "A collaborative task management app for small teams.",
  project_types: ["web_app"],
  stage: "mvp",
  expected_users: "1000",
  generated_at: "2026-01-01T00:00:00Z",
  architecture_summary:
    "A browser client communicates with an API layer backed by application services, " +
    "authentication, and a primary database. Optional components cover file storage, " +
    "async processing, and observability.",
  main_flow: [
    "User interacts with the web client.",
    "Client sends requests to the API layer.",
    "API validates authentication and forwards to application services.",
    "Application services read and write data in the database.",
    "Optional object storage handles uploaded files.",
    "Optional background workers process async jobs.",
    "Monitoring and logging capture operational signals.",
  ],
  architecture_diagrams: {
    high_level: {
      title: "High Level Design",
      nodes: [
        { id: "user", name: "End User", group: "experience" },
        { id: "web_client", name: "Web Client", group: "experience" },
        { id: "api_layer", name: "API Layer", group: "platform" },
        { id: "auth", name: "Authentication Service", group: "platform" },
        { id: "app_service", name: "Application Service", group: "platform" },
        { id: "database", name: "Database", group: "data" },
        { id: "object_storage", name: "File Storage", group: "data" },
      ],
      edges: [
        { source: "user", target: "web_client" },
        { source: "web_client", target: "api_layer" },
        { source: "api_layer", target: "auth" },
        { source: "api_layer", target: "app_service" },
        { source: "app_service", target: "database" },
        { source: "app_service", target: "object_storage" },
      ],
    },
    system_flow: {
      title: "System Flow",
      nodes: [
        { id: "user", name: "User" },
        { id: "sign_in", name: "Sign In" },
        { id: "web_client", name: "Web Client" },
        { id: "upload", name: "Upload File" },
        { id: "object_storage", name: "Object Storage" },
        { id: "process", name: "Process Request" },
        { id: "database", name: "Database" },
        { id: "dashboard", name: "View Dashboard" },
      ],
      edges: [
        { source: "user", target: "sign_in" },
        { source: "sign_in", target: "web_client" },
        { source: "web_client", target: "upload", label: "optional" },
        { source: "upload", target: "object_storage" },
        { source: "web_client", target: "process" },
        { source: "process", target: "database" },
        { source: "database", target: "dashboard" },
      ],
    },
    technical_architecture: {
      title: "Technical Architecture",
      nodes: [
        { id: "user", name: "End User", group: "experience" },
        { id: "web_client", name: "Web Client", group: "experience" },
        { id: "api_layer", name: "API Layer", group: "platform" },
        { id: "auth", name: "Authentication Service", group: "platform" },
        { id: "app_service", name: "Application Service", group: "platform" },
        { id: "database", name: "Database", group: "data" },
        { id: "object_storage", name: "File Storage", group: "data" },
        { id: "monitoring", name: "Monitoring", group: "operations", type: "monitoring" },
        { id: "logging", name: "Logging", group: "operations", type: "logging" },
        { id: "secrets", name: "Secrets Manager", group: "operations", type: "secrets" },
      ],
      edges: [
        { source: "user", target: "web_client" },
        { source: "web_client", target: "api_layer" },
        { source: "api_layer", target: "auth" },
        { source: "api_layer", target: "app_service" },
        { source: "app_service", target: "database" },
        { source: "app_service", target: "object_storage" },
        { source: "api_layer", target: "monitoring" },
        { source: "app_service", target: "logging" },
        { source: "app_service", target: "secrets" },
      ],
    },
  },
};
