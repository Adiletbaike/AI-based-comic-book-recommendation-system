import axios from "axios";
import { API_BASE_URL } from "../utils/constants";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

const looksLikeJwt = (token) => {
  // JWT: 3 base64url-ish segments separated by dots
  if (!token) return false;
  return String(token).split(".").length === 3;
};

const isBadBearer = (value) => {
  if (!value) return true;
  const v = String(value).trim();
  if (!v) return true;
  if (!v.toLowerCase().startsWith("bearer ")) return false;
  const token = v.slice(7).trim();
  if (!token) return true;
  if (token === "null" || token === "undefined") return true;
  return !looksLikeJwt(token);
};

api.interceptors.request.use((config) => {
  // If a bad Authorization header is present, remove it so we don't get 422s from the backend.
  if (config.headers?.Authorization && isBadBearer(config.headers.Authorization)) {
    delete config.headers.Authorization;
  }

  if (!config.headers?.Authorization) {
    const stored = localStorage.getItem("comicai_auth");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        const t = parsed?.token != null ? String(parsed.token).trim() : "";
        const looksLikeJwt = t.split(".").length === 3;
        if (t && t !== "null" && t !== "undefined" && looksLikeJwt) {
          config.headers.Authorization = `Bearer ${t}`;
        }
      } catch (err) {
        return config;
      }
    }
  }
  return config;
});

export const setAuthToken = (token) => {
  const t = token != null ? String(token).trim() : "";
  if (t && t !== "null" && t !== "undefined") {
    api.defaults.headers.common.Authorization = `Bearer ${t}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};
