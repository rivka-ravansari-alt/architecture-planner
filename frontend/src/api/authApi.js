import { apiRequest } from "./client.js";

const AUTH_TIMEOUT_MS = 8_000;

let meRequest = null;

export const authApi = {
  getMe: () => {
    meRequest ??= apiRequest("/auth/me", { timeoutMs: AUTH_TIMEOUT_MS }).finally(() => {
      meRequest = null;
    });
    return meRequest;
  },
  logout: () => apiRequest("/auth/logout", { method: "POST" }),
};
