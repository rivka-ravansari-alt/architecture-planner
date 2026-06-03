const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getMe: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),
  getProjectTypes: () => request("/project-types"),
  createProject: (payload) =>
    request("/projects", { method: "POST", body: JSON.stringify(payload) }),
  generate: (id) => request(`/projects/${id}/generate`, { method: "POST" }),
};
