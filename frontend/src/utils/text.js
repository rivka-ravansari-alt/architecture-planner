export function labelFor(list, id) {
  return list.find((item) => item.id === id)?.label || id;
}

export function truncateToSentences(text, maxSentences = 2) {
  if (!text) return "";
  const trimmed = text.trim();
  const parts = trimmed.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g);
  if (!parts) return trimmed;
  return parts.slice(0, maxSentences).join("").trim();
}

export function formatCloudServices(value) {
  if (Array.isArray(value)) return value.join(", ");
  return value || "—";
}
