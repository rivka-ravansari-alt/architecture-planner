import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/index.js";
import { AUTH_ROUTES } from "../constants/wizard.js";

const AuthContext = createContext(null);
const AUTH_PENDING_KEY = "auth_pending";

function initialLoadingMessage() {
  return sessionStorage.getItem(AUTH_PENDING_KEY) === "1"
    ? "Completing sign-in…"
    : "Checking your session…";
}

function clearAuthPending() {
  sessionStorage.removeItem(AUTH_PENDING_KEY);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState(initialLoadingMessage);

  const refresh = useCallback(async () => {
    try {
      const me = await api.getMe();
      setUser(me ?? null);
      if (me) {
        clearAuthPending();
      }
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await refresh();
      } finally {
        if (!cancelled) {
          clearAuthPending();
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const login = useCallback(() => {
    sessionStorage.setItem(AUTH_PENDING_KEY, "1");
    window.location.href = AUTH_ROUTES.googleLogin;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      clearAuthPending();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, loadingMessage, login, logout }),
    [user, loading, loadingMessage, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
