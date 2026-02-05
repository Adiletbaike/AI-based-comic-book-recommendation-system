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
      const parsed = JSON.parse(stored);
      setToken(parsed.token);
      setUser(parsed.user);
      setAuthToken(parsed.token);
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
