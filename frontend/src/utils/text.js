import { PROVIDER_LABELS } from "../constants/providers.js";

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
  if (value && typeof value === "object") {
    const parts = Object.entries(value)
      .filter(([, service]) => service)
      .map(
        ([provider, service]) =>
          `${PROVIDER_LABELS[provider] ?? provider}: ${service}`
      );
    return parts.length ? parts.join(" · ") : "—";
  }
  return value || "—";
}
