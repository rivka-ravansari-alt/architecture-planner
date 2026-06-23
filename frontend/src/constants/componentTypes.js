import {
  Activity,
  BarChart3,
  Bell,
  Brain,
  Cloud,
  Cog,
  CreditCard,
  Database,
  Globe,
  HardDrive,
  KeyRound,
  Layers,
  Monitor,
  Network,
  Puzzle,
  Search,
  Server,
  Settings,
  Shield,
  Smartphone,
  User,
  Workflow,
} from "lucide-react";

export const COMPONENT_TYPES = [
  "user",
  "web_app",
  "mobile_app",
  "admin_panel",
  "browser_extension",
  "cdn",
  "load_balancer",
  "api",
  "api_gateway",
  "authentication",
  "auth",
  "service",
  "database",
  "object_storage",
  "queue",
  "worker",
  "cache",
  "search",
  "ai_service",
  "ai_provider",
  "monitoring",
  "logging",
  "tracing",
  "alerting",
  "secrets",
  "config",
  "analytics",
  "notification",
  "payment",
  "external_api",
  "integration",
];

/** Canonical types from the LLM component catalog (manual add form). */
export const CATALOG_COMPONENT_TYPES = [
  "user",
  "web_app",
  "mobile_app",
  "admin_panel",
  "cdn",
  "load_balancer",
  "api_gateway",
  "service",
  "worker",
  "database",
  "cache",
  "queue",
  "object_storage",
  "search",
  "external_api",
  "ai_provider",
  "payment",
  "notification",
  "analytics",
  "secrets",
  "config",
  "monitoring",
  "logging",
  "tracing",
  "alerting",
];

export const COMPONENT_TYPE_LABELS = {
  user: "User",
  web_app: "Web App",
  mobile_app: "Mobile App",
  admin_panel: "Admin Panel",
  browser_extension: "Browser Extension",
  cdn: "CDN",
  load_balancer: "Load Balancer",
  api: "API",
  api_gateway: "API Gateway",
  authentication: "Authentication",
  auth: "Auth",
  service: "Service",
  database: "Database",
  object_storage: "Object Storage",
  queue: "Queue",
  worker: "Worker",
  cache: "Cache",
  search: "Search",
  ai_service: "AI Service",
  ai_provider: "AI Provider",
  monitoring: "Monitoring",
  logging: "Logging",
  tracing: "Tracing",
  alerting: "Alerting",
  secrets: "Secrets",
  config: "Config",
  analytics: "Analytics",
  notification: "Notification",
  payment: "Payment",
  external_api: "External API",
  integration: "Integration",
};

/** Default purpose text shown when a catalog type is selected. */
export const COMPONENT_TYPE_DESCRIPTIONS = {
  user: "End users who interact with the product through client applications.",
  web_app: "Browser-based application that delivers the primary user experience.",
  mobile_app: "Native or cross-platform mobile application for iOS and Android devices.",
  admin_panel: "Administrative interface for managing users, content, and configuration.",
  cdn: "Content delivery network that caches and serves static assets close to users.",
  load_balancer:
    "Distributes incoming traffic across service instances for availability and scale.",
  api_gateway:
    "Entry point for client requests, handling routing, authentication, and rate limiting.",
  service: "Core application service that implements business logic and orchestrates data access.",
  worker: "Background processor that handles asynchronous jobs and long-running tasks.",
  database: "Primary data store for structured application data and transactions.",
  cache: "In-memory store that reduces database load and improves read latency.",
  queue: "Message queue that decouples producers and consumers for reliable async processing.",
  object_storage: "Durable storage for files, images, uploads, and other unstructured data.",
  search: "Full-text search index for fast querying across application content.",
  external_api: "Integration with third-party services and partner APIs.",
  ai_provider:
    "External or managed AI/ML service for inference, embeddings, or generative features.",
  payment: "Payment processing for subscriptions, one-time purchases, and billing.",
  notification: "Delivers email, SMS, and push notifications to users.",
  analytics: "Collects usage data and supports reporting, dashboards, and product insights.",
  secrets: "Secure storage and rotation of API keys, credentials, and sensitive configuration.",
  config: "Centralized configuration management across environments and services.",
  monitoring: "Tracks health, performance metrics, and service-level indicators.",
  logging: "Aggregates application and infrastructure logs for troubleshooting.",
  tracing: "Distributed tracing to follow requests across services and diagnose latency.",
  alerting: "Routes monitoring signals to on-call channels when thresholds are breached.",
};

export const COMPONENT_SOURCE_AI = "ai_generated";
export const COMPONENT_SOURCE_USER = "user_added";

export const COMPONENT_SOURCE_LABELS = {
  [COMPONENT_SOURCE_AI]: "AI Generated",
  [COMPONENT_SOURCE_USER]: "User Added",
};

export const DEFAULT_COMPONENT_TYPE = "api_gateway";

const TYPE_ALIASES = {
  api: "api_gateway",
  authentication: "auth",
  ai_service: "ai_provider",
  integration: "external_api",
};

const ICON_MAP = {
  user: User,
  web_app: Monitor,
  mobile_app: Smartphone,
  admin_panel: Monitor,
  browser_extension: Puzzle,
  cdn: Cloud,
  load_balancer: Server,
  api: Network,
  api_gateway: Network,
  authentication: Shield,
  auth: Shield,
  service: Cog,
  database: Database,
  object_storage: HardDrive,
  queue: Workflow,
  worker: Cog,
  cache: Layers,
  search: Search,
  ai_service: Brain,
  ai_provider: Brain,
  monitoring: Activity,
  logging: Activity,
  tracing: Activity,
  alerting: Bell,
  secrets: KeyRound,
  config: Settings,
  analytics: BarChart3,
  notification: Bell,
  payment: CreditCard,
  external_api: Globe,
  integration: Globe,
};

export function getComponentIcon(type) {
  const normalized = normalizeComponentType(type);
  return ICON_MAP[normalized] || ICON_MAP[DEFAULT_COMPONENT_TYPE];
}

export function formatComponentTypeLabel(type) {
  const normalized = normalizeComponentType(type);
  return COMPONENT_TYPE_LABELS[normalized] || normalized.replace(/_/g, " ");
}

export function getComponentTypeDescription(type) {
  const normalized = normalizeComponentType(type);
  return (
    COMPONENT_TYPE_DESCRIPTIONS[normalized] ||
    `Provides ${formatComponentTypeLabel(normalized).toLowerCase()} capabilities for this architecture.`
  );
}

export function getComponentSourceLabel(source) {
  return COMPONENT_SOURCE_LABELS[source] || COMPONENT_SOURCE_LABELS[COMPONENT_SOURCE_AI];
}

export function isUserAddedComponent(component) {
  return component?.source === COMPONENT_SOURCE_USER;
}

export function normalizeComponentType(type) {
  if (!type) {
    return DEFAULT_COMPONENT_TYPE;
  }
  const aliased = TYPE_ALIASES[type] || type;
  if (COMPONENT_TYPES.includes(aliased)) {
    return aliased;
  }
  return DEFAULT_COMPONENT_TYPE;
}
