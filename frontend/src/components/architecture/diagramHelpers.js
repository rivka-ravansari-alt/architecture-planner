/** Canonical diagram keys — add new entries here to support additional diagram types. */
export const DIAGRAM_DEFINITIONS = [
  {
    key: "high_level",
    tabLabel: "High Level Design",
    fallbackTitle: "High Level Design",
    description:
      "Major business components and system boundaries — optimized for quick stakeholder understanding.",
  },
  {
    key: "system_flow",
    tabLabel: "System Flow",
    fallbackTitle: "System Flow",
    description: "How requests and data move through the system from trigger to outcome.",
  },
  {
    key: "technical_flow",
    tabLabel: "Technical Flow",
    fallbackTitle: "Technical Flow",
    description:
      "Internal services, databases, queues, APIs, and infrastructure implementation details.",
  },
];

/**
 * Resolve diagrams from the project payload.
 * Supports the new multi-diagram format and legacy single-diagram data.
 */
export function resolveArchitectureDiagrams(project) {
  const multi = project?.architecture_diagrams;
  if (multi && typeof multi === "object") {
    return DIAGRAM_DEFINITIONS.map(({ key, tabLabel, fallbackTitle, description }) => {
      const diagram = multi[key];
      if (!diagram?.nodes?.length) return null;
      return {
        key,
        tabLabel,
        title: diagram.title || fallbackTitle,
        description,
        diagram,
      };
    }).filter(Boolean);
  }

  const legacy = project?.architecture_diagram;
  if (legacy?.type === "react_flow" && legacy.nodes?.length) {
    return [
      {
        key: "high_level",
        tabLabel: DIAGRAM_DEFINITIONS[0].tabLabel,
        title: "High Level Design",
        description: DIAGRAM_DEFINITIONS[0].description,
        diagram: legacy,
      },
    ];
  }

  if (legacy?.type === "mermaid") {
    return [
      {
        key: "high_level",
        tabLabel: "High Level Design",
        title: "Architecture Diagram",
        description: "",
        diagram: legacy,
      },
    ];
  }

  return [];
}
