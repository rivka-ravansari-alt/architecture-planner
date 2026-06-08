import { apiRequest } from "./client.js";

const AUTH_TIMEOUT_MS = 8_000;

export const authApi = {
  getMe: () => apiRequest("/auth/me", { timeoutMs: AUTH_TIMEOUT_MS }),
  logout: () => apiRequest("/auth/logout", { method: "POST" }),
};
