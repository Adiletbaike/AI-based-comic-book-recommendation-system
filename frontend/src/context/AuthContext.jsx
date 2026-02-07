import React, { createContext, useEffect, useMemo, useState } from "react";
import * as authService from "../services/auth";
import { setAuthToken } from "../services/api";

export const AuthContext = createContext(undefined);

const STORAGE_KEY = "comicai_auth";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        const rawToken = parsed?.token;
        const t = rawToken != null ? String(rawToken).trim() : "";
        const looksLikeJwt = t.split(".").length === 3;
        if (t && t !== "null" && t !== "undefined" && looksLikeJwt) {
          setToken(t);
          setUser(parsed.user || null);
          setAuthToken(t);
        } else {
          localStorage.removeItem(STORAGE_KEY);
          setAuthToken(null);
        }
      } catch (e) {
        localStorage.removeItem(STORAGE_KEY);
        setAuthToken(null);
      }
    }
    setIsReady(true);
  }, []);

  const handleLogin = async (email, password) => {
    const data = await authService.login(email, password);
    setToken(data.access_token);
    setUser(data.user);
    setAuthToken(data.access_token);
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: data.access_token, user: data.user }));
  };

  const handleRegister = async (username, email, password) => {
    await authService.register(username, email, password);
  };

  const handleLogout = async () => {
    await authService.logout();
    setToken(null);
    setUser(null);
    setAuthToken();
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isReady,
      login: handleLogin,
      register: handleRegister,
      logout: handleLogout,
    }),
    [user, token, isReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
