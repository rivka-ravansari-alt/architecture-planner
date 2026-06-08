const NODE_WIDTH = 220;
const NODE_HEIGHT = 88;
const NODE_GAP_X = 20;
const NODE_GAP_Y = 16;
const GROUP_PADDING_X = 20;
const GROUP_PADDING_Y = 22;
const GROUP_LABEL_HEIGHT = 18;
const CANVAS_PADDING = 24;

const DOMAIN_GAP_X = 28;
const DOMAIN_GAP_Y = 32;
const TIER_GAP_Y = 32;
const FLOW_LAYER_GAP_Y = 40;
const MAX_DOMAIN_ROW_WIDTH = 680;

const TIER_ORDER = ["entry", "processing", "infrastructure"];
const PRODUCTION_TIER_ORDER = ["entry", "processing", "data", "observability"];

export const TIER_LABELS = {
  entry: "Clients & Entry Points",
  processing: "Application & Processing",
  infrastructure: "Storage & Infrastructure",
  data: "Data & Content",
  observability: "Infrastructure, Security & Observability",
};

const DOMAIN_ORDER = ["experience", "platform", "data", "operations"];

export const DOMAIN_LABELS = {
  experience: "User Experience",
  platform: "Core Platform",
  data: "Data & Content",
  operations: "Operations & Integrations",
};

const TYPE_TIER = {
  user: "entry",
  web_app: "entry",
  mobile_app: "entry",
  admin_panel: "entry",
  browser_extension: "entry",
  cdn: "entry",
  load_balancer: "entry",
  api: "processing",
  api_gateway: "processing",
  authentication: "processing",
  auth: "processing",
  service: "processing",
  worker: "processing",
  ai_service: "processing",
  ai_provider: "processing",
  analytics: "processing",
  notification: "processing",
  payment: "processing",
  external_api: "processing",
  integration: "processing",
  monitoring: "infrastructure",
  logging: "infrastructure",
  tracing: "infrastructure",
  alerting: "infrastructure",
  secrets: "infrastructure",
  config: "infrastructure",
  cache: "infrastructure",
  database: "infrastructure",
  object_storage: "infrastructure",
  queue: "infrastructure",
  search: "infrastructure",
  backup: "infrastructure",
};

const TYPE_TIER_PRODUCTION = {
  ...TYPE_TIER,
  database: "data",
  object_storage: "data",
  queue: "data",
  cache: "data",
  search: "data",
  monitoring: "observability",
  logging: "observability",
  tracing: "observability",
  alerting: "observability",
  secrets: "observability",
  config: "observability",
};

const TYPE_DOMAIN = {
  user: "experience",
  web_app: "experience",
  mobile_app: "experience",
  admin_panel: "experience",
  browser_extension: "experience",
  cdn: "platform",
  load_balancer: "platform",
  api: "platform",
  api_gateway: "platform",
  authentication: "platform",
  auth: "platform",
  service: "platform",
  worker: "platform",
  ai_service: "platform",
  ai_provider: "platform",
  analytics: "operations",
  notification: "operations",
  payment: "operations",
  external_api: "operations",
  database: "data",
  object_storage: "data",
  queue: "data",
  cache: "data",
  search: "data",
  monitoring: "operations",
  logging: "operations",
  tracing: "operations",
  alerting: "operations",
  secrets: "operations",
  config: "operations",
  integration: "operations",
  backup: "operations",
};

function tierIndex(tier, tierOrder = TIER_ORDER) {
  const index = tierOrder.indexOf(tier);
  return index === -1 ? 1 : index;
}

function tierForComponentType(componentType, typeTierMap = TYPE_TIER) {
  return typeTierMap[componentType] || "processing";
}

function domainForNode(node) {
  if (node.group && DOMAIN_LABELS[node.group]) {
    return node.group;
  }
  return TYPE_DOMAIN[node.componentType] || "platform";
}

function refineTiers(nodes, edges, typeTierMap = TYPE_TIER) {
  const tiers = new Map(
    nodes.map((node) => [node.id, tierForComponentType(node.componentType, typeTierMap)])
  );

  const tierOrder =
    typeTierMap === TYPE_TIER_PRODUCTION ? PRODUCTION_TIER_ORDER : TIER_ORDER;

  for (let pass = 0; pass < nodes.length; pass += 1) {
    for (const edge of edges) {
      if (!tiers.has(edge.source) || !tiers.has(edge.target)) continue;
      const sourceTier = tierIndex(tiers.get(edge.source), tierOrder);
      let targetTier = tierIndex(tiers.get(edge.target), tierOrder);
      const minTarget = Math.min(sourceTier + 1, tierOrder.length - 1);
      if (targetTier < minTarget) {
        targetTier = minTarget;
        tiers.set(edge.target, tierOrder[targetTier]);
      }
    }
  }

  return tiers;
}

function sortNodesInLayer(layerNodes, edges) {
  if (layerNodes.length <= 1) return layerNodes;

  const ids = new Set(layerNodes.map((n) => n.id));
  const inDegree = new Map(layerNodes.map((n) => [n.id, 0]));

  for (const edge of edges) {
    if (ids.has(edge.source) && ids.has(edge.target)) {
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    }
  }

  return [...layerNodes].sort((a, b) => {
    const degreeDiff = (inDegree.get(a.id) || 0) - (inDegree.get(b.id) || 0);
    if (degreeDiff !== 0) return degreeDiff;
    return a.name.localeCompare(b.name);
  });
}

function computeFlowLayers(nodes, edges) {
  const layerById = new Map(nodes.map((node) => [node.id, 0]));

  for (let pass = 0; pass < nodes.length; pass += 1) {
    for (const edge of edges) {
      if (!layerById.has(edge.source) || !layerById.has(edge.target)) continue;
      const nextLayer = layerById.get(edge.source) + 1;
      if (nextLayer > layerById.get(edge.target)) {
        layerById.set(edge.target, nextLayer);
      }
    }
  }

  const layers = new Map();
  for (const node of nodes) {
    const layer = layerById.get(node.id) ?? 0;
    if (!layers.has(layer)) layers.set(layer, []);
    layers.get(layer).push(node);
  }

  return [...layers.entries()].sort(([a], [b]) => a - b);
}

function layoutGroupedRow(label, groupKey, groupNodes, edges, prefix) {
  const sorted = sortNodesInLayer(groupNodes, edges);
  const innerWidth =
    sorted.length * NODE_WIDTH + Math.max(0, sorted.length - 1) * NODE_GAP_X;
  const groupWidth = innerWidth + GROUP_PADDING_X * 2;
  const groupHeight = GROUP_PADDING_Y + GROUP_LABEL_HEIGHT + NODE_HEIGHT + GROUP_PADDING_Y + 6;
  const groupId = `${prefix}-${groupKey}`;

  const children = sorted.map((node, index) => ({
    ...node,
    parentId: groupId,
    position: {
      x: GROUP_PADDING_X + index * (NODE_WIDTH + NODE_GAP_X),
      y: GROUP_PADDING_Y + GROUP_LABEL_HEIGHT,
    },
  }));

  return {
    group: {
      id: groupId,
      label,
      width: groupWidth,
      height: groupHeight,
    },
    children,
  };
}

function centerGroupsHorizontally(groups) {
  if (!groups.length) return;
  const maxWidth = Math.max(...groups.map((g) => g.width));
  for (const group of groups) {
    group.position.x += (maxWidth - group.width) / 2;
  }
}

function layoutTechnicalFlow(nodes, edges, tierOrder = TIER_ORDER, typeTierMap = TYPE_TIER) {
  const tiers = refineTiers(nodes, edges, typeTierMap);
  const byTier = new Map(tierOrder.map((tier) => [tier, []]));

  for (const node of nodes) {
    const tier = tiers.get(node.id) || "processing";
    if (!byTier.has(tier)) byTier.set(tier, []);
    byTier.get(tier).push(node);
  }

  const activeTiers = tierOrder.filter((tier) => byTier.get(tier)?.length > 0);
  const groups = [];
  const positioned = [];
  let currentY = 0;
  let maxGroupWidth = 0;

  for (const tier of activeTiers) {
    const { group, children } = layoutGroupedRow(
      TIER_LABELS[tier],
      tier,
      byTier.get(tier),
      edges,
      "tier"
    );
    maxGroupWidth = Math.max(maxGroupWidth, group.width);
    groups.push({ ...group, position: { x: 0, y: currentY } });
    positioned.push(...children);
    currentY += group.height + TIER_GAP_Y;
  }

  const centerOffset = maxGroupWidth / 2;
  for (const group of groups) {
    group.position.x = centerOffset - group.width / 2;
  }

  return { groups, nodes: positioned };
}

function layoutSystemFlow(nodes, edges) {
  const layerEntries = computeFlowLayers(nodes, edges);
  const positioned = [];
  let currentY = 0;
  let maxLayerWidth = 0;

  for (const [, layerNodes] of layerEntries) {
    const sorted = sortNodesInLayer(layerNodes, edges);
    const layerWidth =
      sorted.length * NODE_WIDTH + Math.max(0, sorted.length - 1) * NODE_GAP_X;
    maxLayerWidth = Math.max(maxLayerWidth, layerWidth);
    let x = -layerWidth / 2;
    for (const node of sorted) {
      positioned.push({
        ...node,
        position: { x, y: currentY },
      });
      x += NODE_WIDTH + NODE_GAP_X;
    }
    currentY += NODE_HEIGHT + FLOW_LAYER_GAP_Y;
  }

  const offsetX = maxLayerWidth / 2;
  for (const node of positioned) {
    node.position.x += offsetX;
  }

  return { groups: [], nodes: positioned };
}

function layoutHighLevel(nodes, edges) {
  const byDomain = new Map(DOMAIN_ORDER.map((domain) => [domain, []]));
  for (const node of nodes) {
    const domain = domainForNode(node);
    if (!byDomain.has(domain)) byDomain.set(domain, []);
    byDomain.get(domain).push(node);
  }

  const activeDomains = DOMAIN_ORDER.filter((domain) => byDomain.get(domain)?.length > 0);
  const groups = [];
  const positioned = [];
  let rowX = 0;
  let rowY = 0;
  let rowMaxHeight = 0;

  for (const domain of activeDomains) {
    const { group, children } = layoutGroupedRow(
      DOMAIN_LABELS[domain],
      domain,
      byDomain.get(domain),
      edges,
      "domain"
    );

    if (rowX > 0 && rowX + group.width > MAX_DOMAIN_ROW_WIDTH) {
      rowY += rowMaxHeight + DOMAIN_GAP_Y;
      rowX = 0;
      rowMaxHeight = 0;
    }

    groups.push({ ...group, position: { x: rowX, y: rowY } });
    positioned.push(...children);
    rowMaxHeight = Math.max(rowMaxHeight, group.height);
    rowX += group.width + DOMAIN_GAP_X;
  }

  const minX = Math.min(...groups.map((g) => g.position.x));
  const maxX = Math.max(...groups.map((g) => g.position.x + g.width));
  const shiftX = -((minX + maxX) / 2);
  for (const group of groups) {
    group.position.x += shiftX;
  }

  return { groups, nodes: positioned };
}

/**
 * Layout nodes using a strategy tuned for the diagram type.
 */
export function layoutDiagramNodes(nodes, edges, diagramType = "high_level") {
  if (!nodes.length) {
    return { groups: [], nodes: [] };
  }

  switch (diagramType) {
    case "high_level":
      return layoutHighLevel(nodes, edges);
    case "system_flow":
      return layoutSystemFlow(nodes, edges);
    case "technical_architecture":
    case "production_architecture":
      return layoutTechnicalFlow(nodes, edges, PRODUCTION_TIER_ORDER, TYPE_TIER_PRODUCTION);
    case "technical_flow":
    default:
      return layoutTechnicalFlow(nodes, edges);
  }
}

export function getFlowBounds(layout) {
  const { groups, nodes } = layout;
  const items = groups?.length ? groups : nodes;

  if (!items?.length) {
    return { width: 400, height: 300, offsetX: 24, offsetY: 24 };
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  if (groups?.length) {
    for (const group of groups) {
      const { x, y } = group.position;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + group.width);
      maxY = Math.max(maxY, y + group.height);
    }
  } else {
    for (const node of nodes) {
      const { x, y } = node.position;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + NODE_WIDTH);
      maxY = Math.max(maxY, y + NODE_HEIGHT);
    }
  }

  const padding = CANVAS_PADDING;
  return {
    width: maxX - minX + padding * 2,
    height: maxY - minY + padding * 2,
    offsetX: -minX + padding,
    offsetY: -minY + padding,
    contentWidth: maxX - minX,
    contentHeight: maxY - minY,
  };
}

export { NODE_WIDTH, NODE_HEIGHT, CANVAS_PADDING };
