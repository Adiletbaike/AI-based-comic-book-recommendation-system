import axios from "axios";
import { API_BASE_URL } from "../utils/constants";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  if (!config.headers?.Authorization) {
    const stored = localStorage.getItem("comicai_auth");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed?.token) {
          config.headers.Authorization = `Bearer ${parsed.token}`;
        }
      } catch (err) {
        return config;
      }
    }
  }
  return config;
});

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};
