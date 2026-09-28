import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { authApi } from "../services/auth";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // The session cookie is httpOnly, so there is nothing to read up front —
    // just ask the server who we are. A 401 simply means "logged out".
    authApi
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { user: authUser } = await authApi.login(email, password);
    setUser(authUser);
  }, []);

  const register = useCallback(async (email: string, username: string, password: string) => {
    const { user: authUser } = await authApi.register(email, username, password);
    setUser(authUser);
  }, []);

  const logout = useCallback(async () => {
    // Clear local state even if the request fails: the user asked to leave, and
    // a stale session on screen is worse than a server-side cookie lingering.
    setUser(null);
    navigate("/");
    try {
      await authApi.logout();
    } catch {
      /* cookie expires on its own */
    }
  }, [navigate]);

  const refreshUser = useCallback(async () => {
    try {
      setUser(await authApi.me());
    } catch {
      /* handled by api interceptor */
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
