import {
  Activity,
  BarChart3,
  Bell,
  Brain,
  Cog,
  CreditCard,
  Database,
  HardDrive,
  Monitor,
  Network,
  Puzzle,
  Shield,
  Smartphone,
  User,
  Workflow,
} from "lucide-react";

/** Canonical component types returned by the AI — icons are UI-only. */
export const COMPONENT_TYPES = [
  "user",
  "web_app",
  "mobile_app",
  "browser_extension",
  "api",
  "authentication",
  "database",
  "object_storage",
  "queue",
  "worker",
  "ai_service",
  "monitoring",
  "analytics",
  "notification",
  "payment",
];

export const DEFAULT_COMPONENT_TYPE = "api";

const ICON_MAP = {
  user: User,
  web_app: Monitor,
  mobile_app: Smartphone,
  browser_extension: Puzzle,
  api: Network,
  authentication: Shield,
  database: Database,
  object_storage: HardDrive,
  queue: Workflow,
  worker: Cog,
  ai_service: Brain,
  monitoring: Activity,
  analytics: BarChart3,
  notification: Bell,
  payment: CreditCard,
};

export function getComponentIcon(type) {
  return ICON_MAP[type] || ICON_MAP[DEFAULT_COMPONENT_TYPE];
}

export function normalizeComponentType(type) {
  if (type && COMPONENT_TYPES.includes(type)) {
    return type;
  }
  return DEFAULT_COMPONENT_TYPE;
}
