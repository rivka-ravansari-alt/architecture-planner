import { apiRequest, GENERATE_TIMEOUT_MS } from "./client.js";

export const projectApi = {
  getProjectTypes: () => apiRequest("/project-types"),
  createProject: (payload) =>
    apiRequest("/projects", { method: "POST", body: JSON.stringify(payload) }),
  generate: (projectId) =>
    apiRequest(`/projects/${projectId}/generate`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),
  generateComponents: (projectId) =>
    apiRequest(`/projects/${projectId}/generate-components`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),
  updateComponents: (projectId, components) =>
    apiRequest(`/projects/${projectId}/components`, {
      method: "PUT",
      body: JSON.stringify({ components }),
    }),
  generateDiagrams: (projectId) =>
    apiRequest(`/projects/${projectId}/generate-diagrams`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),
  approveArchitecture: (projectId) =>
    apiRequest(`/projects/${projectId}/approve-architecture`, { method: "POST" }),
  generatePricing: (projectId) =>
    apiRequest(`/projects/${projectId}/generate-pricing`, {
      method: "POST",
      timeoutMs: GENERATE_TIMEOUT_MS,
    }),
};
