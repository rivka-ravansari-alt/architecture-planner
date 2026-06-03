import { MarkerType } from "@xyflow/react";
import { DEFAULT_COMPONENT_TYPE, normalizeComponentType } from "../../constants/componentTypes.js";
import { getFlowBounds, layoutDiagramNodes } from "./diagramLayout.js";

function componentLookup(components) {
  const byName = new Map();
  for (const component of components || []) {
    byName.set(component.name, component);
  }
  return byName;
}

function inferTypeFromNodeName(name) {
  const lower = name.toLowerCase();
  if (/\b(end\s+)?user\b/.test(lower) || lower === "user") return "user";
  if (lower.includes("mobile")) return "mobile_app";
  if (lower.includes("extension")) return "browser_extension";
  if (lower.includes("browser")) return "web_app";
  if (lower.includes("web") && (lower.includes("client") || lower.includes("application") || lower.includes("app"))) return "web_app";
  if (lower.includes("dashboard") || lower.includes("report")) return "analytics";
  if (lower.includes("object storage") || lower.includes("blob") || (lower.includes("storage") && !lower.includes("processing"))) return "object_storage";
  if (lower.includes("sign in") || lower.includes("login") || lower.includes("auth")) return "authentication";
  if (lower.includes("validation") || lower.includes("verify")) return "authentication";
  if (lower.includes("database") || lower.includes("data store")) return "database";
  if (/\bqueue\b/.test(lower) || lower.includes("processing queue")) return "queue";
  if (/\bprocess\b/.test(lower) || lower.includes("processing")) return "worker";
  if (lower.includes("worker")) return "worker";
  if (lower.includes("monitor")) return "monitoring";
  if (lower.includes("analytic")) return "analytics";
  if (lower.includes("notification")) return "notification";
  if (lower.includes("payment") || lower.includes("billing")) return "payment";
  if (lower.includes("ai ") || lower.includes("llm")) return "ai_service";
  if (lower.includes("api") || lower.includes("gateway")) return "api";
  if (lower.includes("upload")) return "worker";
  if (lower.includes("web")) return "web_app";
  return DEFAULT_COMPONENT_TYPE;
}

export function buildFlowGraph(diagram, components = [], diagramType = "technical_flow") {
  if (!diagram) {
    return null;
  }

  const isLegacyReactFlow = diagram.type === "react_flow";
  const nodes = diagram.nodes || [];
  const edges = diagram.edges || [];
  if (!isLegacyReactFlow && !nodes.length) {
    return null;
  }
  if (isLegacyReactFlow && !nodes.length) {
    return null;
  }

  const lookup = componentLookup(components);
  const enriched = nodes.map((node) => {
    const match = lookup.get(node.name);
    const componentType = normalizeComponentType(
      match?.type || inferTypeFromNodeName(node.name)
    );
    const tag = match?.optional ? "optional" : "required";
    return {
      id: node.id,
      name: node.name,
      componentType,
      tag,
      group: node.group || null,
    };
  });

  const layout = layoutDiagramNodes(enriched, edges, diagramType);
  const bounds = getFlowBounds(layout);

  const flowGroupNodes = layout.groups.map((group) => ({
    id: group.id,
    type: "tierGroup",
    position: {
      x: group.position.x + bounds.offsetX,
      y: group.position.y + bounds.offsetY,
    },
    data: { label: group.label },
    style: {
      width: group.width,
      height: group.height,
    },
    draggable: false,
    selectable: false,
  }));

  const flowNodes = layout.nodes.map((node) => ({
    id: node.id,
    type: "architecture",
    parentId: node.parentId,
    extent: "parent",
    position: node.position,
    data: {
      label: node.name,
      componentType: node.componentType,
      tag: node.tag,
    },
    draggable: false,
    selectable: false,
  }));

  const flowEdges = edges.map((edge, index) => ({
    id: `edge-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#94a3b8" },
    style: { stroke: "#cbd5e1", strokeWidth: 1.5 },
    labelStyle: { fill: "#64748b", fontSize: 11 },
    labelBgStyle: { fill: "#ffffff", fillOpacity: 0.9 },
    animated: false,
  }));

  return {
    nodes: [...flowGroupNodes, ...flowNodes],
    edges: flowEdges,
    bounds,
  };
}
