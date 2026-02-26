import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { fetchJson, getStoredToken, setStoredToken } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearAuth = useCallback(() => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    const stored = getStoredToken();
    if (!stored) {
      setLoading(false);
      setUser(null);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchJson("/api/auth/me");
      setUser(data);
    } catch (error) {
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, [clearAuth]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const handler = () => {
      clearAuth();
    };
    window.addEventListener("auth:unauthorized", handler);
    return () => {
      window.removeEventListener("auth:unauthorized", handler);
    };
  }, [clearAuth]);

  const login = useCallback(async (username, password) => {
    const data = await fetchJson("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    setStoredToken(data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (username, password) => {
    const data = await fetchJson("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    setStoredToken(data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetchJson("/api/auth/logout", { method: "POST" });
    } catch {
      // ignore
    }
    clearAuth();
  }, [clearAuth]);

  const value = useMemo(
    () => ({ token, user, loading, login, register, logout, refresh }),
    [token, user, loading, login, register, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
