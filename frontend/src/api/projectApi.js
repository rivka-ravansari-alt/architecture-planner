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
};
