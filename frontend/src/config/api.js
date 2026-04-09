// API base URL — empty string means relative paths, which Vite proxies to the backend.
// Works identically on localhost and on Replit without any hardcoded URLs.
export const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export const FALLBACK_API_BASE_URL = API_BASE_URL;
