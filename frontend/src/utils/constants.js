export const APP_NAME = "ComicAI";
// Dev default is same-origin so Vite can proxy `/api` to the backend without CORS pain.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
