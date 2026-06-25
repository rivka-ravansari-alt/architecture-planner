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

import {
  getCatalogDescription,
  getCatalogTypeNames,
  getDefaultCatalogType,
} from "./componentCatalog.js";

/** Legacy types kept for normalizing existing project components (mirrors backend LEGACY_COMPONENT_TYPES). */
export const LEGACY_COMPONENT_TYPES = new Set([
  "browser_extension",
  "api",
  "authentication",
  "auth",
  "ai_service",
  "integration",
  "backup",
]);

export const COMPONENT_SOURCE_AI = "ai_generated";
export const COMPONENT_SOURCE_USER = "user_added";

export const COMPONENT_SOURCE_LABELS = {
  [COMPONENT_SOURCE_AI]: "AI Generated",
  [COMPONENT_SOURCE_USER]: "User Added",
};

export const DEFAULT_COMPONENT_TYPE = "api_gateway";

/** Mirrors backend COMPONENT_TYPE_ALIASES. */
const TYPE_ALIASES = {
  api: "api_gateway",
  authentication: "auth",
  ai_service: "ai_provider",
  integration: "external_api",
};

const TYPE_LABEL_OVERRIDES = {
  cdn: "CDN",
  api: "API",
  api_gateway: "API Gateway",
  ai_provider: "AI Provider",
  ai_service: "AI Service",
  external_api: "External API",
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
  backup: HardDrive,
};

function titleCaseType(type) {
  return type.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function getComponentIcon(type) {
  const normalized = normalizeComponentType(type);
  return ICON_MAP[normalized] || ICON_MAP[DEFAULT_COMPONENT_TYPE];
}

export function formatComponentTypeLabel(type) {
  const normalized = normalizeComponentType(type);
  return TYPE_LABEL_OVERRIDES[normalized] || titleCaseType(normalized);
}

export function getComponentTypeDescription(type) {
  const normalized = normalizeComponentType(type);
  return (
    getCatalogDescription(normalized) ||
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
    return getDefaultCatalogType();
  }
  const aliased = TYPE_ALIASES[type] || type;
  const catalogTypes = getCatalogTypeNames();
  if (catalogTypes.includes(aliased)) {
    return aliased;
  }
  if (LEGACY_COMPONENT_TYPES.has(aliased)) {
    return aliased;
  }
  return getDefaultCatalogType();
}
