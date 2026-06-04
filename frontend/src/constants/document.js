export const DOCUMENT_SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "components", label: "Components" },
  { id: "diagrams", label: "Architecture Diagrams" },
  { id: "flow", label: "Architecture Flow" },
  { id: "risks", label: "Risks" },
  { id: "recommendations", label: "Recommendations" },
  { id: "next-steps", label: "Next Steps" },
  { id: "costs", label: "Cloud & Costs" },
];

export const RISK_LEVELS = ["high", "medium", "low"];

export const DIAGRAM_TAB_LABELS = {
  high_level: "High Level",
  system_flow: "System Flow",
  technical_flow: "Technical Flow",
};

export const DIAGRAM_DESCRIPTIONS = {
  high_level: "Business and system-boundary view for stakeholders.",
  system_flow: "Request and data movement through the system.",
  technical_flow: "Internal services, infrastructure, and processing steps.",
};
