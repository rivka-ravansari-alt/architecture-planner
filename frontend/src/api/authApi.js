import { apiRequest } from "./client.js";

const GOOGLE_LOGIN_URL = "/api/auth/google";

export const authApi = {
  /** Start Google OAuth by redirecting the browser to the backend. */
  startGoogleLogin: () => {
    window.location.href = GOOGLE_LOGIN_URL;
  },
  /** Return the current user or null when unauthenticated. */
  getMe: () => apiRequest("/auth/me"),
  logout: () => apiRequest("/auth/logout", { method: "POST" }),
};
