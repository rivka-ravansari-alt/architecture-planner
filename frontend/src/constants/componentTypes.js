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
