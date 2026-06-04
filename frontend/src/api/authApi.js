import { apiRequest } from "./client.js";

export const authApi = {
  getMe: () => apiRequest("/auth/me"),
  logout: () => apiRequest("/auth/logout", { method: "POST" }),
};
