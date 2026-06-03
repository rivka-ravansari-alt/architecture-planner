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

export function truncateToSentences(text, maxSentences = 2) {
  if (!text) return "";
  const trimmed = text.trim();
  const parts = trimmed.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g);
  if (!parts) return trimmed;
  return parts
    .slice(0, maxSentences)
    .join("")
    .trim();
}

export function groupRisksBySeverity(risks = []) {
  const groups = { high: [], medium: [], low: [] };
  for (const risk of risks) {
    const key = risk.severity?.toLowerCase();
    if (key === "high" || key === "medium" || key === "low") {
      groups[key].push(risk);
    } else {
      groups.medium.push(risk);
    }
  }
  return groups;
}

export function formatCloudServices(value) {
  if (Array.isArray(value)) return value.join(", ");
  return value || "—";
}
