import { createContext, useContext, useState, useCallback } from "react";
import api, { extractError } from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [userId, setUserId] = useState(() => localStorage.getItem("sb_user_id"));
  const [token, setToken] = useState(() => localStorage.getItem("sb_token"));

  const login = useCallback(async (email, password) => {
    try {
      const res = await api.post("/auth/login", { email, password });
      localStorage.setItem("sb_token", res.data.access_token);
      localStorage.setItem("sb_user_id", res.data.user_id);
      setToken(res.data.access_token);
      setUserId(res.data.user_id);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: extractError(err) };
    }
  }, []);

  const register = useCallback(async (userIdInput, email, password) => {
    try {
      const res = await api.post("/auth/register", {
        user_id: userIdInput,
        email,
        password,
      });
      localStorage.setItem("sb_token", res.data.access_token);
      localStorage.setItem("sb_user_id", res.data.user_id);
      setToken(res.data.access_token);
      setUserId(res.data.user_id);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: extractError(err) };
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("sb_token");
    localStorage.removeItem("sb_user_id");
    setToken(null);
    setUserId(null);
  }, []);

  return (
    <AuthContext.Provider value={{ userId, token, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
